-- 로그인 사용자별 CRUD 권한 설정: 01_schema.sql 적용 후 한 번 실행합니다.
-- Supabase SQL Editor에서 실행합니다. 앱의 공개 키로 실행하지 않습니다.
-- 테이블/컬럼을 바꾸지 않고 RLS 정책만 추가합니다.
-- 별도의 관리자/판매자 권한 체계는 만들지 않습니다. type은 회원 정보입니다.
-- 교안: 데이터베이스 & AI 활용 3장 7강 4절 (FOR ALL / USING / WITH CHECK).
-- 주문 상품 연결: SQL & 데이터베이스 3장 1강 4절 (IN + 서브쿼리).
-- 중복 이름의 정책이 있으면 오류로 멈추며, 기존 정책은 삭제하지 않습니다.

BEGIN;

-- 회원 상세 정보: auth.users.id와 같은 본인 id만 관리합니다.
CREATE POLICY "회원 본인 정보 관리"
ON public.user_details
FOR ALL
TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- 상품 목록: 로그인한 사용자는 모든 상품을 조회할 수 있습니다.
CREATE POLICY "로그인 사용자 상품 조회"
ON public.products
FOR SELECT
TO authenticated
USING (true);

-- 상품 등록/수정/삭제: seller_id가 본인인 상품만 관리합니다.
-- 수정 후에도 seller_id가 본인이어야 합니다.
CREATE POLICY "본인 상품 관리"
ON public.products
FOR ALL
TO authenticated
USING (auth.uid() = seller_id)
WITH CHECK (auth.uid() = seller_id);

-- 주문: user_id가 본인인 주문만 관리합니다.
CREATE POLICY "본인 주문 관리"
ON public.orders
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 주문 상품: 로그인 사용자의 주문 id 목록에 속하는 내역만 관리합니다.
-- order_id를 다른 사용자의 주문으로 바꾸는 것도 막습니다.
CREATE POLICY "본인 주문 상품 관리"
ON public.order_items
FOR ALL
TO authenticated
USING (
    order_id IN (
        SELECT id
        FROM public.orders
        WHERE user_id = auth.uid()
    )
)
WITH CHECK (
    order_id IN (
        SELECT id
        FROM public.orders
        WHERE user_id = auth.uid()
    )
);

COMMIT;

-- 적용 직후 읽기 전용 확인 (교안 밖 보충: pg_policies 시스템 목록).
-- 정책 5개가 보여야 합니다. 이것은 실제 로그인 CRUD 테스트를 대신하지 않습니다.
SELECT tablename, policyname, cmd, roles, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('user_details', 'products', 'orders', 'order_items')
ORDER BY tablename, policyname;
