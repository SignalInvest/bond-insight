-- docs/SKILL_1035.md Step 1 — Supabase SQL Editor에서 그대로 실행할 것.
-- yunseo/output/통합 데이터.csv(2026-08-07, 359건)를 담을 신규 테이블.
-- bond_market 테이블 패턴(unique(isin_code, reference_date))을 그대로 따라가서
-- 나중에 다른 날짜 CSV가 생겨도 upsert로 누적 가능하게 함.

create table if not exists public.bond_snapshot (
  id bigint generated always as identity primary key,
  isin_code text not null,
  reference_date date not null,
  bond_name text not null,
  issuer text,
  bond_type text,
  credit_rating text,
  issue_date date,
  maturity_date date not null,
  remaining_days integer,
  coupon_rate numeric,
  close_price numeric,
  ytm numeric,
  volume bigint,
  trading_value numeric,
  has_option boolean,
  is_fixed_rate boolean,
  macaulay_duration numeric,
  modified_duration numeric,
  relative_yield_spread numeric,
  created_at timestamptz not null default now(),
  unique (isin_code, reference_date)
);

create index if not exists bond_snapshot_isin_idx on public.bond_snapshot (isin_code);
create index if not exists bond_snapshot_reference_date_idx on public.bond_snapshot (reference_date);

alter table public.bond_snapshot enable row level security;

-- docs/database-erd.md 정책과 동일: anon/authenticated는 조회만 허용, 적재는 백엔드 Secret Key로만.
drop policy if exists "bond_snapshot_read_all" on public.bond_snapshot;
create policy "bond_snapshot_read_all"
  on public.bond_snapshot
  for select
  to anon, authenticated
  using (true);

-- SQL Editor로 만든 테이블은 Table Editor(UI)로 만든 테이블과 달리 service_role에 권한이
-- 자동으로 안 붙는 경우가 있다 — 없으면 "permission denied for table bond_snapshot" 에러가 남.
-- (id는 GENERATED ALWAYS AS IDENTITY라 내부 시퀀스에 별도 GRANT 불필요)
grant select, insert, update, delete on public.bond_snapshot to service_role;
grant select on public.bond_snapshot to anon, authenticated;
