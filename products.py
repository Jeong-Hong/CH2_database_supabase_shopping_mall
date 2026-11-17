# 교안: 데이터베이스 & AI 활용 3장 3~5강의 SDK CRUD와 3장 7강의 사용자별 접근.
# seller_id는 로그인 사용자에게서 가져오고, 수정/삭제에는 id와 seller_id 조건을 함께 붙입니다.
# 수정할 때 modified_at도 KST 실행 환경의 현재 시각으로 갱신합니다.
from members import get_current_user_id
from time_utils import current_modified_at

MAX_PRICE = 2 ** 31 - 1


def validate_product(name, price):
    if not name.strip():
        raise ValueError("상품명을 입력합니다.")
    if type(price) != int or price < 0 or price > MAX_PRICE:
        raise ValueError(f"가격은 0부터 {MAX_PRICE}까지의 정수로 입력합니다.")


def get_products(supabase, only_mine=False):
    user_id = get_current_user_id(supabase)
    query = supabase.table("products").select("*")
    if only_mine:
        query = query.eq("seller_id", user_id)
    response = query.order("created_at", desc=True).execute()
    return response.data


def get_product(supabase, product_id, only_mine=False):
    if not product_id:
        raise ValueError("상품 ID를 입력합니다.")
    user_id = get_current_user_id(supabase)
    query = supabase.table("products").select("*").eq("id", product_id)
    if only_mine:
        query = query.eq("seller_id", user_id)
    return query.execute().data


def create_product(supabase, name, description, price):
    validate_product(name, price)
    user_id = get_current_user_id(supabase)
    current_time = current_modified_at()
    response = supabase.table("products").insert({
        "created_at": current_time,
        "modified_at": current_time,
        "name": name.strip(),
        "description": description,
        "price": price,
        "seller_id": user_id,
    }).execute()
    return response.data


def update_product(supabase, product_id, name, description, price):
    if not product_id:
        raise ValueError("상품 ID를 입력합니다.")
    validate_product(name, price)
    user_id = get_current_user_id(supabase)
    response = (
        supabase.table("products")
        .update({"name": name.strip(), "description": description, "price": price,
                 "modified_at": current_modified_at()})
        .eq("id", product_id)
        .eq("seller_id", user_id)
        .execute()
    )
    return response.data


def delete_product(supabase, product_id):
    if not product_id:
        raise ValueError("상품 ID를 입력합니다.")
    user_id = get_current_user_id(supabase)
    response = (
        supabase.table("products")
        .delete()
        .eq("id", product_id)
        .eq("seller_id", user_id)
        .execute()
    )
    return response.data


def print_products(rows):
    if not rows:
        print("조회된 상품이 없습니다.")
        return
    for row in rows:
        print("---")
        print("상품 ID:", row["id"])
        print("상품명:", row["name"])
        print("설명:", row["description"])
        print("가격:", row["price"])
        print("판매자 ID:", row["seller_id"])
        print("생성 시각:", row["created_at"])
        print("수정 시각:", row["modified_at"])


def product_menu(supabase):
    while True:
        print("\n=== 상품 메뉴 ===")
        print("1. 등록")
        print("2. 전체 상품 조회")
        print("3. 내 상품 조회")
        print("4. 내 상품 수정")
        print("5. 내 상품 삭제")
        print("0. 이전 메뉴")
        choice = input("메뉴 선택: ").strip()

        if choice == "0":
            return
        if choice not in ("1", "2", "3", "4", "5"):
            print("메뉴에 표시된 번호를 입력합니다.")
            continue

        try:
            if choice == "2":
                print_products(get_products(supabase))
                continue
            if choice == "3":
                print_products(get_products(supabase, only_mine=True))
                continue

            if choice in ("4", "5"):
                product_id = input("상품 ID: ").strip()
                current = get_product(supabase, product_id, only_mine=True)
                if not current:
                    print("내 상품에서 해당 상품을 찾지 못했습니다.")
                    continue
                print_products(current)

            if choice in ("1", "4"):
                name = input("상품명 (필수): ").strip()
                if not name:
                    print("상품명을 입력합니다.")
                    continue
                description = input("설명: ").strip()
                price_text = input("가격 (0 이상 정수): ").strip()
                try:
                    price = int(price_text)
                except ValueError:
                    print("가격은 정수로 입력합니다.")
                    continue
                validate_product(name, price)

                if choice == "1":
                    rows = create_product(supabase, name, description, price)
                    if rows:
                        print("상품 등록 완료")
                        print_products(get_product(supabase, rows[0]["id"], only_mine=True))
                    else:
                        print("등록 결과를 확인하지 못했습니다.")
                else:
                    rows = update_product(supabase, product_id, name, description, price)
                    if rows:
                        print("상품 수정 완료")
                        print_products(get_product(supabase, product_id, only_mine=True))
                    else:
                        print("수정할 내 상품을 찾지 못했습니다.")

            elif choice == "5":
                confirm = input("상품을 삭제하려면 DELETE 입력: ").strip()
                if confirm != "DELETE":
                    print("삭제를 취소했습니다.")
                    continue
                rows = delete_product(supabase, product_id)
                if not rows:
                    print("삭제할 내 상품을 찾지 못했습니다.")
                    continue
                check = get_product(supabase, product_id, only_mine=True)
                if not check:
                    print("상품 삭제 완료. 재조회 결과가 없습니다.")
                else:
                    print("삭제 후에도 상품이 조회됩니다. 결과를 확인합니다.")

        except ValueError as error:
            print("입력 오류:", error)
        except Exception as error:
            print("상품 요청 실패:", type(error).__name__)
            print("상품 ID, 로그인 상태, 접근 권한을 확인합니다.")
            print("주의: 주문 상품이 참조하는 상품은 삭제할 수 없습니다.")
