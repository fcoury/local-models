use task::truncate_utf8;
#[test] fn ordinary() { assert_eq!(truncate_utf8("hello", 3), "hel"); }
#[test] fn partial_character() { assert_eq!(truncate_utf8("éclair", 1), ""); }
