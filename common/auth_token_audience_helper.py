import tldextract


def process_localutm(subdomain: str, domain: str) -> str:
    uss_audience = subdomain + "." + domain
    return uss_audience


def generate_audience_from_base_url(base_url: str) -> str:
    switch = {
        "localhost": "localhost",
        "internal": "host.docker.internal",
        "test": "local.test",
        "localutm": "scdsc.uss2.localutm",  # TODO: Fix this, this need not be hard coded
    }
    try:
        ext = tldextract.extract(base_url)
    except Exception:
        uss_audience = "localhost"
    else:
        if ext.domain in [
            "localhost",
            "internal",
            "test",
        ]:  # for host.docker.internal type calls
            uss_audience = switch[ext.domain]
        elif ext.domain in ["localutm"]:
            uss_audience = process_localutm(subdomain=ext.subdomain, domain=ext.domain)
        else:
            if ext.suffix in (""):
                uss_audience = ext.domain
            else:
                uss_audience = ".".join(ext[:3])  # get the subdomain, domain and suffix and create a audience and get credentials
    return uss_audience
