-- 쇼핑몰 테이블 생성: 과제용 새 Supabase 프로젝트에서 한 번 실행합니다.
-- auth.users는 Supabase가 관리합니다. 직접 만들거나 변경하지 않습니다.
-- 기존 테이블이 있으면 오류로 멈춥니다. 기존 테이블을 삭제하지 않습니다.
-- 원본과 합의한 차이: orders.deleted_at은 NULL을 허용합니다.
-- 기본값: 상품/주문/주문 상품 id 자동 생성, 생성/수정 시각 최초 저장 시 자동 입력.
-- user_details.id는 회원가입 결과의 user.id를 전달합니다.
-- modified_at은 앱의 수정 코드에서 갱신합니다. 앱 실행 환경은 KST이며 자동 갱신 트리거는 없습니다.
-- ON DELETE RESTRICT: 참조 중인 부모 행의 물리 삭제를 막습니다.
-- RLS는 켜지만 정책은 아직 만들지 않습니다. SDK CRUD 권한은 다음 단계에서 설정합니다.
-- 교안: 데이터베이스 & AI 활용 1장 3강, 5강, 6강 / 2장 5강 / 3장 7강.

BEGIN;

CREATE TABLE public.user_details (
    id uuid PRIMARY KEY,
    type text NOT NULL,
    cellphone text,
    zipcode text,
    address text,
    address_sub text,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT user_details_id_fkey
        FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE RESTRICT
);

CREATE TABLE public.products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    description text NOT NULL,
    price int4 NOT NULL,
    seller_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT products_seller_id_fkey
        FOREIGN KEY (seller_id) REFERENCES auth.users(id) ON DELETE RESTRICT
);

CREATE TABLE public.orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_no text UNIQUE,
    order_name text NOT NULL,
    order_email text NOT NULL,
    order_phone text NOT NULL,
    receiver_name text NOT NULL,
    receiver_phone text NOT NULL,
    zipcode text NOT NULL,
    address text NOT NULL,
    address_sub text NOT NULL,
    delivery_memo text,
    total_price int4,
    order_status text,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    user_id uuid,
    CONSTRAINT orders_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE RESTRICT
);

CREATE TABLE public.order_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id uuid,
    product_id uuid,
    item_name text NOT NULL,
    price int4 NOT NULL,
    quantity int4 NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT order_items_order_id_fkey
        FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE RESTRICT,
    CONSTRAINT order_items_product_id_fkey
        FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT
);

ALTER TABLE public.user_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;

COMMIT;
