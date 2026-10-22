use task::parse_port;
#[test] fn boundaries() {
 for (s,v) in [("1",1),("0001",1),("65535",65535),("80",80)] { assert_eq!(parse_port(s),Some(v)); }
 for s in ["", "0", "000", "65536", "99999999999999999999", "+80", "-1", " 80", "80 ", "８０", "8x"] { assert_eq!(parse_port(s),None, "{s}"); }
}
