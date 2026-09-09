-- ============================================================
-- Le Chai Gourmand - abonnes a la lettre d'information
-- et suivi des courriels de reservation
--
-- A coller dans Supabase -> SQL Editor -> Run. Rejouable sans risque.
-- ============================================================

create extension if not exists pgcrypto;

-- ---------- abonnes ----------
create table if not exists public.abonnes (
  id         uuid primary key default gen_random_uuid(),
  cree_le    timestamptz not null default now(),
  email      text not null,
  statut     text not null default 'actif' check (statut in ('actif', 'desinscrit')),
  source     text,                                   -- 'site', 'agenda', 'reservation'
  jeton      text not null default encode(gen_random_bytes(16), 'hex'),
  desinscrit_le timestamptz
);

-- une seule ligne par adresse : un reabonnement met a jour l'existante
create unique index if not exists abonnes_email_idx on public.abonnes (lower(email));
create unique index if not exists abonnes_jeton_idx on public.abonnes (jeton);

-- ---------- traces des courriels envoyes ----------
-- Evite d'envoyer deux fois la meme confirmation si Adrien reclique.
alter table public.reservations add column if not exists confirmation_envoyee timestamptz;
alter table public.reservations add column if not exists annulation_envoyee   timestamptz;

-- Evite d'annoncer deux fois le meme evenement aux abonnes.
alter table public.evenements add column if not exists annonce_envoyee timestamptz;
alter table public.evenements add column if not exists annonce_nombre  integer;

-- ---------- droits ----------
-- Personne ne lit la liste des abonnes depuis le navigateur public :
-- les inscriptions passent par la fonction serveur, la lecture demande un compte.
alter table public.abonnes enable row level security;

drop policy if exists "abonnes: lecture equipe" on public.abonnes;
drop policy if exists "abonnes: gestion equipe" on public.abonnes;
create policy "abonnes: lecture equipe" on public.abonnes
  for select to authenticated using (true);
create policy "abonnes: gestion equipe" on public.abonnes
  for all to authenticated using (true) with check (true);

select 'migration courriels ok' as resultat,
       (select count(*) from public.abonnes) as abonnes;
