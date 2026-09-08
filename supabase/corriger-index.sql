-- ============================================================
-- Correction : l'index unique sur « reference » etait partiel
-- (where reference is not null), et PostgreSQL refuse d'utiliser
-- un index partiel pour un ON CONFLICT. L'import echouait donc.
--
-- Un index unique simple suffit : PostgreSQL considere les valeurs
-- NULL comme distinctes, les fiches ajoutees depuis le back-office
-- (sans reference) ne se genent donc pas entre elles.
--
-- A coller dans Supabase -> SQL Editor -> Run.
-- ============================================================

drop index if exists public.produits_reference_idx;

create unique index produits_reference_idx
  on public.produits (reference);

select indexname, indexdef
  from pg_indexes
 where schemaname = 'public' and tablename = 'produits';
