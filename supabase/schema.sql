-- ============================================================
-- Le Chai Gourmand — base du back-office
-- À coller tel quel dans Supabase → SQL Editor → Run.
-- Ré-exécutable sans risque : tout est en « if not exists ».
-- ============================================================

create extension if not exists pgcrypto;

-- ---------- réservations (écrites par la fonction /api/reserver) ----------
create table if not exists public.reservations (
  id          uuid primary key default gen_random_uuid(),
  cree_le     timestamptz not null default now(),
  lieu        text not null check (lieu in ('francazal', 'annexe')),
  date        date not null,
  heure       text not null,                       -- « 19:30 »
  couverts    integer not null check (couverts between 1 and 40),
  nom         text not null,
  telephone   text not null,
  email       text,
  message     text,
  statut      text not null default 'nouvelle'
              check (statut in ('nouvelle', 'confirmee', 'annulee')),
  note_interne text
);
create index if not exists reservations_date_idx on public.reservations (date, heure);

-- ---------- événements (saisis dans le back-office) ----------
create table if not exists public.evenements (
  id          uuid primary key default gen_random_uuid(),
  cree_le     timestamptz not null default now(),
  date        date not null,
  heure       text not null default '',            -- texte libre : « dès 17h », « 21h – 1h »
  lieu        text not null check (lieu in ('francazal', 'annexe')),
  titre       text not null,
  description text not null default '',
  reservation boolean not null default false,      -- « sur réservation »
  statut      text not null default 'brouillon'
              check (statut in ('brouillon', 'publie'))
);
create index if not exists evenements_date_idx on public.evenements (date);

-- ---------- produits ajoutés depuis le back-office ----------
-- Le catalogue principal reste généré depuis data/produits.json ; ces
-- fiches-ci s'y ajoutent au chargement de la page.
create table if not exists public.produits (
  id          uuid primary key default gen_random_uuid(),
  cree_le     timestamptz not null default now(),
  nom         text not null,
  type        text not null check (type in
              ('rouge','blanc','rose','bulles','moelleux','biere','spiritueux','epicerie')),
  producteur  text,
  appellation text,
  origine     text,
  cepages     text,
  millesime   text,
  alcool      text,
  contenance  text,
  visuel      text,
  nez         text,
  bouche      text,
  accords     text,
  phrase      text,
  photo       text,                                -- URL publique dans le bucket « produits »
  statut      text not null default 'brouillon'
              check (statut in ('brouillon', 'publie'))
);

-- ---------- droits ----------
-- Tout le monde lit ce qui est publié ; seuls les comptes connectés écrivent.
-- Les réservations n'entrent que par la fonction serveur (clé de service).
alter table public.reservations enable row level security;
alter table public.evenements   enable row level security;
alter table public.produits     enable row level security;

drop policy if exists "reservations: lecture équipe"  on public.reservations;
drop policy if exists "reservations: écriture équipe" on public.reservations;
create policy "reservations: lecture équipe"  on public.reservations
  for select to authenticated using (true);
create policy "reservations: écriture équipe" on public.reservations
  for update to authenticated using (true) with check (true);

drop policy if exists "evenements: lecture publique" on public.evenements;
drop policy if exists "evenements: tout pour l'équipe" on public.evenements;
create policy "evenements: lecture publique" on public.evenements
  for select to anon using (statut = 'publie');
create policy "evenements: tout pour l'équipe" on public.evenements
  for all to authenticated using (true) with check (true);

drop policy if exists "produits: lecture publique" on public.produits;
drop policy if exists "produits: tout pour l'équipe" on public.produits;
create policy "produits: lecture publique" on public.produits
  for select to anon using (statut = 'publie');
create policy "produits: tout pour l'équipe" on public.produits
  for all to authenticated using (true) with check (true);

-- ---------- photos des produits ----------
insert into storage.buckets (id, name, public)
  values ('produits', 'produits', true)
  on conflict (id) do nothing;

drop policy if exists "photos produits: lecture publique" on storage.objects;
drop policy if exists "photos produits: dépôt équipe"     on storage.objects;
create policy "photos produits: lecture publique" on storage.objects
  for select to anon, authenticated using (bucket_id = 'produits');
create policy "photos produits: dépôt équipe" on storage.objects
  for insert to authenticated with check (bucket_id = 'produits');

-- ---------- programmation de septembre 2026, reprise du site ----------
insert into public.evenements (date, heure, lieu, titre, description, reservation, statut)
select * from (values
  ('2026-09-03'::date, 'dès 17h', 'francazal', 'Afterwork Latino',
   'Le comptoir passe à l''heure latine — tapas, verres et rythmes qui réchauffent.', false, 'publie'),
  ('2026-09-04', 'dès 17h · quizz à 21h', 'francazal', 'Afterwork French Party + Quizz Culture Générale',
   'Chanson française à l''apéro, puis quizz spécial rentrée scolaire pour départager les tablées.', false, 'publie'),
  ('2026-09-05', '21h', 'francazal', 'Concert — David Soul',
   'Concert live au Chai, un verre à la main.', false, 'publie'),
  ('2026-09-10', 'dès 17h', 'francazal', 'Afterwork Soirée années 2000',
   'La bande-son de vos années lycée, les planches en plus.', false, 'publie'),
  ('2026-09-10', 'en soirée', 'annexe', 'Initiation à la dégustation — vins d''Espagne',
   'Soirée accords mets & vins autour des vins d''Espagne, guidée par le caviste.', true, 'publie'),
  ('2026-09-11', 'dès 17h · blind test à 21h', 'francazal', 'Afterwork House + Blind Test',
   'House à l''apéro, blind test à 21h — venez en équipe.', false, 'publie'),
  ('2026-09-12', 'dès 21h', 'francazal', 'Concert de saxophone & Soirée Blanche',
   'Sax en live et dress code blanc pour finir l''été en beauté.', false, 'publie'),
  ('2026-09-17', 'dès 17h', 'francazal', 'Afterwork Rap & RnB US',
   'Le comptoir en mode US — planches, verres et classiques du genre.', false, 'publie'),
  ('2026-09-18', '21h – 1h', 'francazal', 'DJ Nana',
   'DJ set au Chai jusqu''au bout de la nuit.', false, 'publie'),
  ('2026-09-24', 'dès 17h', 'francazal', 'Afterwork Disco / Funk',
   'Paillettes sonores et verres bien accordés.', false, 'publie'),
  ('2026-09-24', 'en soirée', 'annexe', 'Initiation à la dégustation — vins de Bourgogne',
   'Soirée accords mets & vins autour des vins de Bourgogne, guidée par le caviste.', true, 'publie'),
  ('2026-09-25', 'dès 17h · concert à 20h', 'francazal', 'Afterwork Rock + Concert Free O''Clock',
   'Apéro rock puis concert live de Free O''Clock.', false, 'publie')
) as v(date, heure, lieu, titre, description, reservation, statut)
where not exists (select 1 from public.evenements);
