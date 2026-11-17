# 교안: 데이터베이스 & AI 활용 3장 3~5강의 SDK CRUD를 회원 테이블에 적용합니다.
# 사용자 ID는 입력받지 않고 현재 로그인 사용자에게서 가져옵니다.
# 삭제 대상은 user_details 행입니다. auth.users 계정은 삭제하지 않습니다.
# 수정할 때 modified_at도 KST 실행 환경의 현재 시각으로 갱신합니다.
from time_utils import current_modified_at


def get_current_user_id(supabase):
    response = supabase.auth.get_user()
    if response is None or response.user is None:
        raise ValueError("로그인이 필요합니다.")
    return response.user.id


def get_member_details(supabase):
    user_id = get_current_user_id(supabase)
    response = (
        supabase.table("user_details")
        .select("*")
        .eq("id", user_id)
        .execute()
    )
    return response.data


def create_member_details(supabase, member_type, cellphone, zipcode, address, address_sub):
    if not member_type.strip():
        raise ValueError("회원 유형을 입력합니다.")
    user_id = get_current_user_id(supabase)
    current_time = current_modified_at()
    response = supabase.table("user_details").insert({
        "created_at": current_time,
        "modified_at": current_time,
        "id": user_id,
        "type": member_type.strip(),
        "cellphone": cellphone or None,
        "zipcode": zipcode or None,
        "address": address or None,
        "address_sub": address_sub or None,
    }).execute()
    return response.data


def update_member_details(supabase, member_type, cellphone, zipcode, address, address_sub):
    if not member_type.strip():
        raise ValueError("회원 유형을 입력합니다.")
    user_id = get_current_user_id(supabase)
    response = (
        supabase.table("user_details")
        .update({
            "modified_at": current_modified_at(),
            "type": member_type.strip(),
            "cellphone": cellphone or None,
            "zipcode": zipcode or None,
            "address": address or None,
            "address_sub": address_sub or None,
        })
        .eq("id", user_id)
        .execute()
    )
    return response.data


def delete_member_details(supabase):
    user_id = get_current_user_id(supabase)
    response = (
        supabase.table("user_details")
        .delete()
        .eq("id", user_id)
        .execute()
    )
    return response.data


def print_member_details(rows):
    if not rows:
        print("등록된 회원 상세 정보가 없습니다.")
        return
    for row in rows:
        print("회원 ID:", row["id"])
        print("회원 유형:", row["type"])
        print("전화번호:", row["cellphone"])
        print("우편번호:", row["zipcode"])
        print("주소:", row["address"])
        print("상세 주소:", row["address_sub"])
        print("생성 시각:", row["created_at"])
        print("수정 시각:", row["modified_at"])


def member_menu(supabase):
    while True:
        print("\n=== 회원 상세 정보 메뉴 ===")
        print("1. 등록")
        print("2. 조회")
        print("3. 수정")
        print("4. 삭제 (로그인 계정은 유지)")
        print("0. 이전 메뉴")
        choice = input("메뉴 선택: ").strip()

        if choice == "0":
            return
        if choice not in ("1", "2", "3", "4"):
            print("메뉴에 표시된 번호를 입력합니다.")
            continue

        try:
            if choice == "2":
                print_member_details(get_member_details(supabase))
                continue

            if choice in ("1", "3"):
                current = get_member_details(supabase)
                if choice == "1" and current:
                    print("이미 등록된 정보가 있습니다. 수정 메뉴를 사용합니다.")
                    continue
                if choice == "3" and not current:
                    print("수정할 회원 상세 정보가 없습니다. 먼저 등록합니다.")
                    continue
                if choice == "3":
                    print_member_details(current)
                    print("입력한 값으로 수정합니다. 선택 항목을 비우면 기존 값을 지웁니다.")
                member_type = input("회원 유형 (필수): ").strip()
                if not member_type:
                    print("회원 유형을 입력합니다.")
                    continue
                cellphone = input("전화번호 (선택): ").strip()
                zipcode = input("우편번호 (선택): ").strip()
                address = input("주소 (선택): ").strip()
                address_sub = input("상세 주소 (선택): ").strip()
                if choice == "1":
                    rows = create_member_details(supabase, member_type, cellphone, zipcode, address, address_sub)
                    if rows:
                        print("회원 상세 정보 등록 완료")
                    else:
                        print("등록 결과를 확인하지 못했습니다.")
                else:
                    rows = update_member_details(supabase, member_type, cellphone, zipcode, address, address_sub)
                    if rows:
                        print("회원 상세 정보 수정 완료")
                    else:
                        print("수정 대상을 찾지 못했습니다.")
                print_member_details(get_member_details(supabase))

            elif choice == "4":
                current = get_member_details(supabase)
                if not current:
                    print("삭제할 회원 상세 정보가 없습니다.")
                    continue
                confirm = input("상세 정보만 삭제합니다. 진행하려면 DELETE 입력: ").strip()
                if confirm != "DELETE":
                    print("삭제를 취소했습니다.")
                    continue
                rows = delete_member_details(supabase)
                if rows:
                    print("회원 상세 정보 삭제 완료. 로그인 계정은 유지합니다.")
                else:
                    print("삭제 대상을 찾지 못했습니다.")
                print_member_details(get_member_details(supabase))

        except ValueError as error:
            print(error)
        except Exception as error:
            print("회원 정보 요청 실패:", type(error).__name__)
            print("로그인 상태와 데이터 접근 권한을 확인합니다.")
