# Authorized scopes

Supported kinds are domain, subdomain, IP, CIDR, URL, and URL subtree. Hostnames are lowercased, trailing dots removed, and IDNs converted to ASCII. Domain boundaries are label-aware, so `notexample.com` does not match `example.com`; URL subtrees respect path boundaries, so `/api2` does not match `/api`.

No active matching scope means a hard denial. A disabled or deleted scope cannot authorize a job.
