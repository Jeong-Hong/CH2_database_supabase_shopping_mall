import os

from dotenv import load_dotenv
from supabase import create_client
from members import member_menu
from products import product_menu
from orders import order_menu


def create_connection():
    # 교안 3장 2강: 연결 정보를 코드 밖의 .env에서 불러옵니다.
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")

    if not url or not key:
        raise ValueError("Supabase 연결 정보가 없습니다.")

    return create_client(url, key)


def main():
    try:
        supabase = create_connection()
    except Exception as error:
        print("연결 초기화 실패:", type(error).__name__)
        print(".env의 SUPABASE_URL과 SUPABASE_PUBLISHABLE_KEY를 확인합니다.")
        return

    logged_in = False

    while True:
        print("\n=== 쇼핑몰 인증 메뉴 ===")
        print("1. 회원가입 요청")
        print("2. 로그인")
        print("3. 현재 로그인 사용자 확인")
        print("4. 로그아웃")
        print("5. 회원 상세 정보 CRUD")
        print("6. 상품 CRUD")
        print("7. 주문 및 주문 상품 CRUD")
        print("0. 종료")
        choice = input("메뉴 선택: ").strip()

        if choice == "0":
            print("프로그램을 종료합니다.")
            break

        if choice not in ("1", "2", "3", "4", "5", "6", "7"):
            print("메뉴에 표시된 번호를 입력합니다.")
            continue

        if choice in ("1", "2"):
            if logged_in:
                print("이미 로그인했습니다. 먼저 로그아웃합니다.")
                continue

            # 교안의 환경변수 방식으로 테스트 계정의 비밀번호도 숨깁니다.
            email = os.environ.get("SUPABASE_TEST_EMAIL")
            password = os.environ.get("SUPABASE_TEST_PASSWORD")
            if not email or not password:
                print(".env에 SUPABASE_TEST_EMAIL과 SUPABASE_TEST_PASSWORD를 입력합니다.")
                continue

        try:
            if choice == "1":
                # 교안 3장 6강: 회원가입 요청. 응답 객체와 토큰은 출력하지 않습니다.
                response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                })
                print("회원가입 요청을 보냈습니다.")
                if response.user is not None and response.session is not None:
                    logged_in = True
                    print("현재 프로젝트 설정에서 로그인 세션도 발급되었습니다.")
                else:
                    print("로그인 세션이 없습니다. 이메일 확인 설정과 계정 상태를 확인합니다.")
                    print("이미 가입한 계정이면 로그인 메뉴를 사용합니다.")

            elif choice == "2":
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })
                if response.user is None or response.session is None:
                    print("요청 실패: 로그인 사용자 또는 세션을 확인하지 못했습니다.")
                    continue
                logged_in = True
                print("로그인 성공")
                print("사용자 ID:", response.user.id)

            elif choice == "3":
                if not logged_in:
                    print("로그인한 사용자가 없습니다.")
                    continue
                user = supabase.auth.get_user().user
                if user is None:
                    logged_in = False
                    print("로그인한 사용자를 확인하지 못했습니다.")
                else:
                    print("현재 사용자 ID:", user.id)

            elif choice == "4":
                if not logged_in:
                    print("로그인한 사용자가 없습니다.")
                    continue
                supabase.auth.sign_out()
                logged_in = False
                print("로그아웃 완료")

            elif choice == "5":
                if not logged_in:
                    print("회원 상세 정보 메뉴는 로그인 후 사용할 수 있습니다.")
                    continue
                member_menu(supabase)

            elif choice == "6":
                if not logged_in:
                    print("상품 메뉴는 로그인 후 사용할 수 있습니다.")
                    continue
                product_menu(supabase)

            elif choice == "7":
                if not logged_in:
                    print("주문 메뉴는 로그인 후 사용할 수 있습니다.")
                    continue
                order_menu(supabase)

        except Exception as error:
            # 원문 오류나 Auth 응답에는 비밀 정보가 담길 수 있으므로 출력하지 않습니다.
            print("요청 실패:", type(error).__name__)
            print("계정 정보, 이메일 확인 여부, 인터넷 연결을 확인합니다.")


if __name__ == "__main__":
    main()
