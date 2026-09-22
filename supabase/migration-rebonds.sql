-- ============================================================
-- Le Chai Gourmand - rebonds de courriels
--
-- Brevo previent par webhook quand un message n'arrive pas. On garde la
-- trace du rebond sur la reservation ou sur l'abonne concerne.
--
-- A coller dans Supabase -> SQL Editor -> Run. Rejouable sans risque.
-- ============================================================

-- ---------- reservations ----------
-- Une confirmation qui rebondit : Adrien doit rappeler le client.
alter table public.reservations add column if not exists courriel_rebond       timestamptz;
alter table public.reservations add column if not exists courriel_rebond_motif text;

-- ---------- abonnes ----------
-- Une adresse morte qu'on continue d'arroser abime la reputation de
-- l'expediteur : les messages suivants partent en indesirables, y compris
-- ceux des adresses valides. On sort donc l'adresse de la liste.
alter table public.abonnes add column if not exists rebond_le    timestamptz;
alter table public.abonnes add column if not exists rebond_motif text;

-- Le statut accepte une valeur de plus. La contrainte etait posee en ligne a
-- la creation de la table : son nom depend de Postgres, on la cherche.
do $$
declare nom text;
begin
  select conname into nom
    from pg_constraint
   where conrelid = 'public.abonnes'::regclass
     and contype = 'c'
     and pg_get_constraintdef(oid) ilike '%statut%';
  if nom is not null then
    execute format('alter table public.abonnes drop constraint %I', nom);
  end if;
end $$;

alter table public.abonnes
  add constraint abonnes_statut_check
  check (statut in ('actif', 'desinscrit', 'rebond'));

select 'migration rebonds ok' as resultat,
       (select count(*) from public.abonnes where statut = 'rebond') as abonnes_en_rebond,
       (select count(*) from public.reservations where courriel_rebond is not null) as reservations_en_rebond;
