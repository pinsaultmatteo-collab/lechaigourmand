// Configuration publique du site — à renseigner une fois Supabase créé.
// Ces deux valeurs sont faites pour être vues par le navigateur : la clé
// « anon » ne donne que les droits définis dans supabase/schema.sql
// (lire ce qui est publié). La clé de service, elle, reste sur Vercel.
window.CHAI = {
  supabaseUrl: "https://xdbudbqqwfyfcivnvqzu.supabase.co",
  supabaseAnonKey: "",    // Project settings → API → anon public
};
