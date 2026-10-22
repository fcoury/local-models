use crate::{normalize_tag,TagError};
pub fn render_tags(tags: &[&str]) -> Result<String,TagError> {
 tags.iter().map(|s| normalize_tag(s)).collect::<Result<Vec<_>,_>>().map(|v| v.join(","))
}
