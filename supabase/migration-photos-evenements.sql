-- ============================================================
-- Le Chai Gourmand - une photo par evenement
--
-- L'URL publique de la photo, deposee depuis le back-office dans le
-- stockage " produits " (dossier evenements/), deja ouvert en lecture
-- publique et en depot pour l'equipe connectee.
--
-- A coller dans Supabase -> SQL Editor -> Run. Rejouable sans risque.
-- ============================================================

alter table public.evenements add column if not exists image text;

select 'migration photos evenements ok' as resultat,
       (select count(*) from public.evenements) as evenements;
