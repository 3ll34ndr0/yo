// DNS for marso.ar — source of truth. Applied to Cloudflare by .github/workflows/dns.yml.
// Anything NOT listed here gets deleted on `dnscontrol push`.

var REG_NONE = NewRegistrar("none");
var DSP_CLOUDFLARE = NewDnsProvider("cloudflare");

var GH_USER = "3ll34ndr0"; // 🔧 your GitHub username

D("marso.ar", REG_NONE,
	DnsProvider(DSP_CLOUDFLARE),
	DefaultTTL(1), // 1 = "auto" in Cloudflare

	// --- GitHub Pages (apex). DNS-only (grey cloud) so GitHub can issue the cert. ---
	A("@", "185.199.108.153"),
	A("@", "185.199.109.153"),
	A("@", "185.199.110.153"),
	A("@", "185.199.111.153"),
	AAAA("@", "2606:50c0:8000::153"),
	AAAA("@", "2606:50c0:8001::153"),
	AAAA("@", "2606:50c0:8002::153"),
	AAAA("@", "2606:50c0:8003::153"),

	// --- www + domain verification ---
	// www redirects to apex (GitHub handles the redirect)
	CNAME("www", GH_USER + ".github.io."),
	// 🔧 Uncomment with the value from GitHub → Settings → Pages → "Add a verified domain"
	TXT("_github-pages-challenge-" + GH_USER, "d48d83ee9c94de5ef5d6bd8e1c18f5"),

	// --- Pre-existing records (imported 2026-10-01 with get-zones) ---
	A("argocd", "66.94.113.102"),
	A("fer", "154.53.46.23"),
	A("odoo", "66.94.113.102"),
	A("prvsn", "154.53.46.23"),
	A("sms.fer", "154.53.46.23"),
	A("t", "66.94.113.102", CF_PROXY_ON),
	A("xn--tailands-h1a", "66.94.113.102", CF_PROXY_ON), // tailandés
	SRV("_sip._udp.prueba", 0, 5, 5060, "sbc-usw.delightvoip.com."),
	SRV("_sip._udp.prueba", 0, 5, 5060, "couch2-usw.delightvoip.com."),
);
