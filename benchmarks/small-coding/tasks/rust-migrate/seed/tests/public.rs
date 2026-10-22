use task::{normalize_tag, TagError};
#[test] fn formats() { assert_eq!(task::service::render_tags(&[" Alpha ","BETA"]), Ok("alpha,beta".into())); }
#[test] fn empty_is_error() { assert_eq!(normalize_tag("  "), Err(TagError::Empty)); }
