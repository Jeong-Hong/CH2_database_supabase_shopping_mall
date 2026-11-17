-- 아래 모든 쿼리는 읽기 전용입니다. 테이블이나 데이터는 변경하지 않습니다.
-- 1번은 교안 1장 4강의 information_schema.columns 조회를 확장했습니다.
-- 2~4번은 교안 밖 보충: PostgreSQL 시스템 목록에서 PK/FK, RLS, 정책을 확인합니다.
-- 쿼리는 하나씩 선택해 실행하고 각 결과를 확인합니다.

-- 1. 컬럼 이름/타입/NULL 허용 여부/기본값
SELECT table_name, column_name, udt_name AS data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('user_details', 'products', 'orders', 'order_items')
ORDER BY table_name, ordinal_position;

-- 2. PK/FK/UNIQUE와 참조 대상, 삭제 옵션
SELECT cl.relname AS table_name,
       co.conname AS constraint_name,
       co.contype AS constraint_type,
       pg_get_constraintdef(co.oid) AS definition
FROM pg_constraint AS co
JOIN pg_class AS cl ON cl.oid = co.conrelid
JOIN pg_namespace AS ns ON ns.oid = cl.relnamespace
WHERE ns.nspname = 'public'
  AND cl.relname IN ('user_details', 'products', 'orders', 'order_items')
  AND co.contype IN ('p', 'f', 'u')
ORDER BY cl.relname, co.contype, co.conname;
-- constraint_type: p = PK, f = FK, u = UNIQUE

-- 3. 테이블의 RLS 활성화 여부: rowsecurity가 모두 true여야 합니다.
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('user_details', 'products', 'orders', 'order_items')
ORDER BY tablename;

-- 4. 정책 확인: 01_schema.sql만 적용하면 0개, 02_rls.sql까지 적용하면 5개입니다.
SELECT tablename, policyname, cmd, roles, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('user_details', 'products', 'orders', 'order_items')
ORDER BY tablename, policyname;
