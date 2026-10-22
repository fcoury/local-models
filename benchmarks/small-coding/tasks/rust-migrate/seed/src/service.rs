use crate::normalize_tag;
pub fn render_tags(tags: &[&str]) -> String {
    tags.iter().map(|s| normalize_tag(s)).collect::<Vec<_>>().join(",")
}
