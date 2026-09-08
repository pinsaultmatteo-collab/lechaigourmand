-- Repare les accents des 12 evenements de septembre.
-- Le premier import est passe par un presse-papiers mal encode ;
-- les caracteres accentues y ont ete abimes. Rien n'est supprime : on corrige le texte.
-- A coller dans Supabase -> SQL Editor -> Run.

update public.evenements set titre = 'Afterwork Latino', description = 'Le comptoir passe à l''heure latine — tapas, verres et rythmes qui réchauffent.', heure = 'dès 17h', reservation = false
  where date = '2026-09-03' and lieu = 'francazal';
update public.evenements set titre = 'Afterwork French Party + Quizz Culture Générale', description = 'Chanson française à l''apéro, puis quizz spécial rentrée scolaire pour départager les tablées.', heure = 'dès 17h · quizz à 21h', reservation = false
  where date = '2026-09-04' and lieu = 'francazal';
update public.evenements set titre = 'Concert — David Soul', description = 'Concert live au Chai, un verre à la main.', heure = '21h', reservation = false
  where date = '2026-09-05' and lieu = 'francazal';
update public.evenements set titre = 'Afterwork Soirée années 2000', description = 'La bande-son de vos années lycée, les planches en plus.', heure = 'dès 17h', reservation = false
  where date = '2026-09-10' and lieu = 'francazal';
update public.evenements set titre = 'Afterwork House + Blind Test', description = 'House à l''apéro, blind test à 21h — venez en équipe.', heure = 'dès 17h · blind test à 21h', reservation = false
  where date = '2026-09-11' and lieu = 'francazal';
update public.evenements set titre = 'Concert de saxophone & Soirée Blanche', description = 'Sax en live et dress code blanc pour finir l''été en beauté.', heure = 'dès 21h', reservation = false
  where date = '2026-09-12' and lieu = 'francazal';
update public.evenements set titre = 'Afterwork Rap & RnB US', description = 'Le comptoir en mode US — planches, verres et classiques du genre.', heure = 'dès 17h', reservation = false
  where date = '2026-09-17' and lieu = 'francazal';
update public.evenements set titre = 'DJ Nana', description = 'DJ set au Chai jusqu''au bout de la nuit.', heure = '21h – 1h', reservation = false
  where date = '2026-09-18' and lieu = 'francazal';
update public.evenements set titre = 'Afterwork Disco / Funk', description = 'Paillettes sonores et verres bien accordés.', heure = 'dès 17h', reservation = false
  where date = '2026-09-24' and lieu = 'francazal';
update public.evenements set titre = 'Afterwork Rock + Concert Free O''Clock', description = 'Apéro rock puis concert live de Free O''Clock.', heure = 'dès 17h · concert à 20h', reservation = false
  where date = '2026-09-25' and lieu = 'francazal';
update public.evenements set titre = 'Initiation à la dégustation — vins d''Espagne', description = 'Soirée accords mets & vins autour des vins d''Espagne, guidée par le caviste.', heure = 'en soirée', reservation = true
  where date = '2026-09-10' and lieu = 'annexe';
update public.evenements set titre = 'Initiation à la dégustation — vins de Bourgogne', description = 'Soirée accords mets & vins autour des vins de Bourgogne, guidée par le caviste.', heure = 'en soirée', reservation = true
  where date = '2026-09-24' and lieu = 'annexe';

select date, lieu, titre from public.evenements order by date;
