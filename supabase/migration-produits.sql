-- ============================================================
-- Le Chai Gourmand - la table produits accueille tout le catalogue
--
-- Les 254 fiches vivaient dans un fichier du depot ; elles passent en base
-- pour qu'Adrien puisse les corriger lui-meme. Il manquait six colonnes.
-- A coller dans Supabase -> SQL Editor -> Run. Sans risque, rejouable.
-- ============================================================

alter table public.produits add column if not exists reference     text;  -- identifiant d'origine, stable
alter table public.produits add column if not exists style         text;
alter table public.produits add column if not exists vieillissement text;
alter table public.produits add column if not exists sources       jsonb not null default '[]'::jsonb;
alter table public.produits add column if not exists images        jsonb not null default '[]'::jsonb;
alter table public.produits add column if not exists lot           text;
alter table public.produits add column if not exists prix          text;
alter table public.produits add column if not exists rang          integer;  -- ordre d'affichage, laisse libre

-- une fiche par reference : l'import peut etre rejoue sans creer de doublons
-- index simple et non partiel : un index partiel ne peut pas servir a un
-- ON CONFLICT, et l'import s'en sert pour ne pas creer de doublons.
-- Les NULL sont distincts en PostgreSQL : les fiches sans reference cohabitent.
create unique index if not exists produits_reference_idx
  on public.produits (reference);

-- la colonne photo (une seule URL) est remplacee par images (plusieurs) ;
-- on la garde pour ne rien casser, mais elle n'est plus alimentee.
comment on column public.produits.photo is 'obsolete - utiliser images';

select 'migration ok' as resultat,
       count(*) as colonnes
  from information_schema.columns
 where table_schema = 'public' and table_name = 'produits';
