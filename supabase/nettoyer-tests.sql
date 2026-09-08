-- Supprime les reservations de test creees le 01/09/2026 lors de la recette.
-- Verifiez d'abord ce qui va partir :
select id, date, heure, nom, telephone from public.reservations
  where nom like 'ZZ TEST%';

-- Puis supprimez :
delete from public.reservations where nom like 'ZZ TEST%';
