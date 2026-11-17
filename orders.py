# 교안: 데이터베이스 & AI 활용 3장 3~5강 SDK CRUD, 3장 7~8강 사용자별 접근/통합.
# 여러 execute() 호출은 하나의 트랜잭션이 아닙니다.
# 주문 상품 변경 후 합계 저장 실패 시 재계산 메뉴로 복구합니다.
# 상품명/가격은 주문 상품 추가 시점의 값으로 저장하며, 이후 상품 변경을 따라가지 않습니다.
# 주문 정보/합계/주문 상품 수량 수정 시 modified_at도 갱신합니다. KST 실행 환경 기준입니다.
from members import get_current_user_id
from products import get_product, MAX_PRICE
from time_utils import current_modified_at

ORDER_INPUT_FIELDS = (
    ("order_no", "주문번호 (선택)"),
    ("order_name", "주문자 이름"),
    ("order_email", "주문자 이메일"),
    ("order_phone", "주문자 전화번호"),
    ("receiver_name", "수령인 이름"),
    ("receiver_phone", "수령인 전화번호"),
    ("zipcode", "우편번호"),
    ("address", "주소"),
    ("address_sub", "상세 주소 (없으면 비움)"),
    ("delivery_memo", "배송 메모 (선택)"),
    ("order_status", "주문 상태 (등록 시 비우면 접수)"),
)
REQUIRED_ORDER_FIELDS = (
    "order_name", "order_email", "order_phone", "receiver_name",
    "receiver_phone", "zipcode", "address",
)
OPTIONAL_ORDER_FIELDS = ("order_no", "delivery_memo", "order_status")


def build_order_data(order_info):
    data = {}
    for field, label in ORDER_INPUT_FIELDS:
        value = order_info.get(field)
        if field == "address_sub" and value is None:
            value = ""
        if field in OPTIONAL_ORDER_FIELDS and value == "":
            value = None
        if field in REQUIRED_ORDER_FIELDS:
            if type(value) != str or not value.strip():
                raise ValueError(f"{label}을 입력합니다.")
        elif value is not None and type(value) != str:
            raise ValueError(f"{label}은 문자열로 입력합니다.")
        data[field] = value.strip() if type(value) == str else value
    return data


def get_orders(supabase):
    user_id = get_current_user_id(supabase)
    return (
        supabase.table("orders").select("*")
        .eq("user_id", user_id).order("created_at", desc=True).execute().data
    )


def get_order(supabase, order_id):
    if not order_id:
        raise ValueError("주문 ID를 입력합니다.")
    user_id = get_current_user_id(supabase)
    return (
        supabase.table("orders").select("*")
        .eq("id", order_id).eq("user_id", user_id).execute().data
    )


def require_order(supabase, order_id):
    rows = get_order(supabase, order_id)
    if not rows:
        raise ValueError("내 주문에서 해당 주문을 찾지 못했습니다.")
    return rows[0]


def create_order(supabase, order_info):
    data = build_order_data(order_info)
    data["user_id"] = get_current_user_id(supabase)
    data["total_price"] = 0
    if data["order_status"] is None:
        data["order_status"] = "접수"
    current_time = current_modified_at()
    data["created_at"] = current_time
    data["modified_at"] = current_time
    return supabase.table("orders").insert(data).execute().data


def update_order(supabase, order_id, order_info):
    data = build_order_data(order_info)
    data["modified_at"] = current_modified_at()
    if not order_id:
        raise ValueError("주문 ID를 입력합니다.")
    user_id = get_current_user_id(supabase)
    return (
        supabase.table("orders").update(data)
        .eq("id", order_id).eq("user_id", user_id).execute().data
    )


def get_order_items(supabase, order_id):
    require_order(supabase, order_id)
    return (
        supabase.table("order_items").select("*").eq("order_id", order_id)
        .order("created_at", desc=True).execute().data
    )


def get_order_item(supabase, order_id, item_id):
    require_order(supabase, order_id)
    if not item_id:
        raise ValueError("주문 상품 ID를 입력합니다.")
    return (
        supabase.table("order_items").select("*")
        .eq("order_id", order_id).eq("id", item_id).execute().data
    )


def validate_quantity(quantity):
    if type(quantity) != int or quantity < 1 or quantity > MAX_PRICE:
        raise ValueError(f"수량은 1부터 {MAX_PRICE}까지의 정수로 입력합니다.")


def validate_total(total):
    if total < 0 or total > MAX_PRICE:
        raise ValueError("주문 금액이 int4 저장 범위를 벗어납니다. 수량을 줄입니다.")


def calculate_total(items):
    total = 0
    for item in items:
        validate_quantity(item["quantity"])
        if type(item["price"]) != int or item["price"] < 0 or item["price"] > MAX_PRICE:
            raise ValueError("주문 상품의 가격을 확인합니다.")
        total += item["price"] * item["quantity"]
    validate_total(total)
    return total


def recalculate_order_total(supabase, order_id):
    total = calculate_total(get_order_items(supabase, order_id))
    user_id = get_current_user_id(supabase)
    rows = (
        supabase.table("orders").update({"total_price": total, "modified_at": current_modified_at()})
        .eq("id", order_id).eq("user_id", user_id).execute().data
    )
    if not rows:
        raise ValueError("합계를 저장할 내 주문을 찾지 못했습니다.")
    return rows


def refresh_total_after_change(supabase, order_id):
    try:
        recalculate_order_total(supabase, order_id)
    except Exception:
        raise RuntimeError("주문 상품 변경은 반영됐지만 합계 갱신에 실패했습니다. 합계 재계산 메뉴를 실행합니다.")


def add_order_item(supabase, order_id, product_id, quantity):
    validate_quantity(quantity)
    require_order(supabase, order_id)
    product_rows = get_product(supabase, product_id)
    if not product_rows:
        raise ValueError("해당 상품을 찾지 못했습니다.")
    product = product_rows[0]
    data = {
        "order_id": order_id, "product_id": product["id"],
        "item_name": product["name"], "price": product["price"], "quantity": quantity,
    }
    calculate_total(get_order_items(supabase, order_id) + [data])
    current_time = current_modified_at()
    data["created_at"] = current_time
    data["modified_at"] = current_time
    rows = supabase.table("order_items").insert(data).execute().data
    if rows:
        refresh_total_after_change(supabase, order_id)
    return rows


def update_order_item(supabase, order_id, item_id, quantity):
    validate_quantity(quantity)
    current = get_order_item(supabase, order_id, item_id)
    if not current:
        return []
    previous = current[0]
    total = calculate_total(get_order_items(supabase, order_id))
    total = total - previous["price"] * previous["quantity"] + previous["price"] * quantity
    validate_total(total)
    rows = (
        supabase.table("order_items").update({"quantity": quantity, "modified_at": current_modified_at()})
        .eq("order_id", order_id).eq("id", item_id).execute().data
    )
    if rows:
        refresh_total_after_change(supabase, order_id)
    return rows


def delete_order_item(supabase, order_id, item_id):
    require_order(supabase, order_id)
    if not item_id:
        raise ValueError("주문 상품 ID를 입력합니다.")
    rows = (
        supabase.table("order_items").delete()
        .eq("order_id", order_id).eq("id", item_id).execute().data
    )
    if rows:
        refresh_total_after_change(supabase, order_id)
    return rows


def delete_order(supabase, order_id):
    require_order(supabase, order_id)
    if get_order_items(supabase, order_id):
        raise ValueError("주문 상품을 먼저 삭제합니다. 상품 내역이 있는 주문은 삭제하지 않습니다.")
    user_id = get_current_user_id(supabase)
    return (
        supabase.table("orders").delete()
        .eq("id", order_id).eq("user_id", user_id).execute().data
    )


def print_orders(rows):
    if not rows:
        print("조회된 주문이 없습니다.")
        return
    for row in rows:
        print("---")
        print("주문 ID:", row["id"])
        for field, label in ORDER_INPUT_FIELDS:
            print(label + ":", row[field])
        print("주문 금액:", row["total_price"])
        print("주문자 사용자 ID:", row["user_id"])
        print("생성 시각:", row["created_at"])
        print("수정 시각:", row["modified_at"])


def print_order_items(rows):
    if not rows:
        print("조회된 주문 상품이 없습니다.")
        return
    for row in rows:
        print("---")
        print("주문 상품 ID:", row["id"])
        print("상품 ID:", row["product_id"])
        print("주문 당시 상품명:", row["item_name"])
        print("주문 당시 가격:", row["price"])
        print("수량:", row["quantity"])
        print("상품 금액:", row["price"] * row["quantity"])
        print("생성 시각:", row["created_at"])
        print("수정 시각:", row["modified_at"])


def read_order_input(current=None):
    data = {}
    if current is not None:
        print("빈 입력은 기존 값을 유지합니다. 선택 항목은 '-'로 지울 수 있습니다.")
    for field, label in ORDER_INPUT_FIELDS:
        value = input(label + ": ").strip()
        if current is not None and value == "":
            data[field] = current[field]
        elif value == "-" and field in OPTIONAL_ORDER_FIELDS:
            data[field] = None
        elif value == "-" and field == "address_sub":
            data[field] = ""
        else:
            data[field] = value
    return data


def order_items_menu(supabase, order_id):
    require_order(supabase, order_id)
    while True:
        print("\n=== 주문 상품 메뉴 ===")
        print("주문 ID:", order_id)
        print("1. 상품 추가")
        print("2. 주문 상품 조회")
        print("3. 수량 수정")
        print("4. 주문 상품 삭제")
        print("5. 합계 재계산")
        print("0. 이전 메뉴")
        choice = input("메뉴 선택: ").strip()
        if choice == "0":
            return
        if choice not in ("1", "2", "3", "4", "5"):
            print("메뉴에 표시된 번호를 입력합니다.")
            continue
        try:
            if choice == "1":
                product_id = input("상품 ID: ").strip()
                quantity = int(input("수량 (1 이상 정수): ").strip())
                rows = add_order_item(supabase, order_id, product_id, quantity)
                if rows:
                    print("주문 상품 추가 완료")
                    print_order_items(get_order_items(supabase, order_id))
                    print_orders(get_order(supabase, order_id))
                else:
                    print("추가 결과를 확인하지 못했습니다.")
            elif choice == "2":
                print_order_items(get_order_items(supabase, order_id))
                print_orders(get_order(supabase, order_id))
            elif choice == "3":
                item_id = input("주문 상품 ID: ").strip()
                quantity = int(input("새 수량 (1 이상 정수): ").strip())
                rows = update_order_item(supabase, order_id, item_id, quantity)
                if rows:
                    print("수량 수정 완료")
                    print_order_items(get_order_item(supabase, order_id, item_id))
                    print_orders(get_order(supabase, order_id))
                else:
                    print("수정할 주문 상품을 찾지 못했습니다.")
            elif choice == "4":
                item_id = input("주문 상품 ID: ").strip()
                if not get_order_item(supabase, order_id, item_id):
                    print("삭제할 주문 상품을 찾지 못했습니다.")
                    continue
                if input("삭제하려면 DELETE 입력: ").strip() != "DELETE":
                    print("삭제를 취소했습니다.")
                    continue
                rows = delete_order_item(supabase, order_id, item_id)
                if rows and not get_order_item(supabase, order_id, item_id):
                    print("주문 상품 삭제 완료")
                    print_orders(get_order(supabase, order_id))
                else:
                    print("삭제 결과를 확인하지 못했습니다.")
            elif choice == "5":
                print_orders(recalculate_order_total(supabase, order_id))
                print("합계 재계산 완료")
        except (ValueError, RuntimeError) as error:
            print("주문 상품 작업 안내:", error)
        except Exception as error:
            print("주문 상품 요청 실패:", type(error).__name__)
            print("주문/상품 ID, 로그인 상태, 접근 권한을 확인합니다.")


def order_menu(supabase):
    while True:
        print("\n=== 주문 메뉴 ===")
        print("1. 주문 등록")
        print("2. 내 주문 조회")
        print("3. 주문 정보 수정")
        print("4. 주문 삭제 (주문 상품 먼저 삭제)")
        print("5. 주문 상품 관리")
        print("6. 합계 재계산")
        print("0. 이전 메뉴")
        choice = input("메뉴 선택: ").strip()
        if choice == "0":
            return
        if choice not in ("1", "2", "3", "4", "5", "6"):
            print("메뉴에 표시된 번호를 입력합니다.")
            continue
        try:
            if choice == "1":
                rows = create_order(supabase, read_order_input())
                if rows:
                    print("주문 등록 완료. 상품은 주문 상품 관리 메뉴에서 추가합니다.")
                    print_orders(get_order(supabase, rows[0]["id"]))
                else:
                    print("등록 결과를 확인하지 못했습니다.")
            elif choice == "2":
                print_orders(get_orders(supabase))
            else:
                order_id = input("주문 ID: ").strip()
                current = require_order(supabase, order_id)
                if choice == "3":
                    print_orders([current])
                    rows = update_order(supabase, order_id, read_order_input(current))
                    if rows:
                        print("주문 수정 완료")
                        print_orders(get_order(supabase, order_id))
                    else:
                        print("수정할 주문을 찾지 못했습니다.")
                elif choice == "4":
                    if get_order_items(supabase, order_id):
                        print("주문 상품을 먼저 삭제합니다.")
                        continue
                    if input("주문을 삭제하려면 DELETE 입력: ").strip() != "DELETE":
                        print("삭제를 취소했습니다.")
                        continue
                    rows = delete_order(supabase, order_id)
                    if rows and not get_order(supabase, order_id):
                        print("주문 삭제 완료")
                    else:
                        print("삭제 결과를 확인하지 못했습니다.")
                elif choice == "5":
                    order_items_menu(supabase, order_id)
                elif choice == "6":
                    print_orders(recalculate_order_total(supabase, order_id))
                    print("합계 재계산 완료")
        except (ValueError, RuntimeError) as error:
            print("주문 작업 안내:", error)
        except Exception as error:
            print("주문 요청 실패:", type(error).__name__)
            print("주문 ID, 로그인 상태, 접근 권한을 확인합니다.")
