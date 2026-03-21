from __future__ import annotations

from collections import defaultdict

from cert_catalog import CERT_BLUEPRINTS, catalog_domains, catalog_provider
from question_bank_extra import EXTRA_QUESTION_BANK


EXAM_DOMAINS = {
    "CCNA": [
        "Network Fundamentals",
        "Network Access",
        "IP Connectivity",
        "IP Services",
        "Security Fundamentals",
        "Automation & Programmability",
    ],
    "AZ-900": [
        "Cloud Concepts",
        "Core Azure Services",
        "Azure Management & Governance",
        "Identity & Security",
    ],
    "AZ-800": [
        "Hybrid Identity",
        "Windows Server Administration",
        "Active Directory",
        "File & Storage",
        "Networking",
        "Security",
        "Monitoring & Recovery",
    ],
    "Security+": [
        "General Security Concepts",
        "Threats & Vulnerabilities",
        "Security Architecture",
        "Security Operations",
        "Governance & Risk",
    ],
    "Network+": [
        "Networking Concepts",
        "Network Implementation",
        "Network Operations",
        "Network Security",
        "Troubleshooting",
    ],
}
for exam, domains in catalog_domains().items():
    EXAM_DOMAINS.setdefault(exam, domains)


QUESTION_BANK = {
    "CCNA": {
        "Network Fundamentals": [
            {
                "concept": "OSI model",
                "correct": "The Network layer is responsible for logical addressing and routing packets between networks.",
                "distractors": [
                    "The Data Link layer assigns IP addresses to hosts.",
                    "The Session layer handles frame forwarding with MAC addresses.",
                    "The Physical layer encrypts packets before transmission.",
                ],
                "explanation": "Layer 3 handles IP addressing and routing decisions between distinct networks.",
                "summary": ["Layer 3 is where routers make forwarding decisions.", "IP addresses live at the Network layer."],
                "key_terms": ["OSI", "Layer 3", "routing", "IP addressing"],
                "memory_tip": "Think L3 = location across networks.",
            },
            {
                "concept": "Ethernet frame",
                "correct": "A source MAC address in an Ethernet frame identifies the sending interface on the local segment.",
                "distractors": [
                    "A source MAC address identifies the remote router on the destination network.",
                    "A source MAC address is used only after NAT translation occurs.",
                    "A source MAC address stays unchanged across every routed hop.",
                ],
                "explanation": "MAC addressing is local to the segment and changes hop by hop when routed.",
                "summary": ["MAC addresses matter on the local link.", "Routers rewrite Layer 2 headers each hop."],
                "key_terms": ["MAC", "Ethernet", "frame", "local segment"],
                "memory_tip": "MAC is local, IP is end-to-end.",
            },
        ],
        "Network Access": [
            {
                "concept": "VLAN trunking",
                "correct": "An 802.1Q trunk carries traffic for multiple VLANs across one physical link.",
                "distractors": [
                    "An access port removes the need for VLAN assignments.",
                    "A routed port forwards broadcasts between VLANs by default.",
                    "A trunk can only transport a native VLAN and one tagged VLAN.",
                ],
                "explanation": "Trunks use tagging so multiple VLANs can share a single interface.",
                "summary": ["Trunks extend VLANs between switches.", "802.1Q tagging identifies VLAN membership."],
                "key_terms": ["802.1Q", "trunk", "VLAN", "native VLAN"],
                "memory_tip": "Trunks travel with tags.",
            },
            {
                "concept": "Spanning Tree",
                "correct": "STP prevents Layer 2 loops by placing redundant links into a blocking state.",
                "distractors": [
                    "STP balances traffic by splitting frames across duplicate paths.",
                    "STP assigns default gateways to end devices.",
                    "STP replaces VLAN tagging on access links.",
                ],
                "explanation": "Without STP, switching loops create broadcast storms and MAC table instability.",
                "summary": ["STP keeps one active forwarding path in a looped topology.", "Redundant links stay available for failover."],
                "key_terms": ["STP", "blocking", "loop prevention", "root bridge"],
                "memory_tip": "STP stops storms before they start.",
            },
        ],
        "IP Connectivity": [
            {
                "concept": "static routing",
                "correct": "A static route manually defines the next hop or exit interface for remote networks.",
                "distractors": [
                    "A static route automatically updates metrics when links fail.",
                    "A static route learns networks only through hello packets.",
                    "A static route replaces the ARP table for local delivery.",
                ],
                "explanation": "Static routes are manually configured and do not adapt automatically like dynamic routing.",
                "summary": ["Static routes are predictable and low overhead.", "They require manual maintenance."],
                "key_terms": ["static route", "next hop", "exit interface"],
                "memory_tip": "Static means you own every path change.",
            },
            {
                "concept": "OSPF",
                "correct": "OSPF is a link-state routing protocol that uses cost as its primary metric.",
                "distractors": [
                    "OSPF is a distance-vector protocol that relies only on hop count.",
                    "OSPF uses MAC addresses to build its routing table.",
                    "OSPF advertises VLAN numbers instead of networks.",
                ],
                "explanation": "OSPF builds a topology database and calculates best paths using SPF and interface cost.",
                "summary": ["OSPF converges with topology awareness.", "Cost usually reflects bandwidth."],
                "key_terms": ["OSPF", "link-state", "cost", "SPF"],
                "memory_tip": "OSPF sees the map, then picks the path.",
            },
        ],
        "IP Services": [
            {
                "concept": "NAT",
                "correct": "PAT allows many inside hosts to share one public IP by translating source ports.",
                "distractors": [
                    "PAT maps one public IP to one inside host with no port changes.",
                    "PAT is used only for inbound static server publishing.",
                    "PAT disables routing between inside and outside networks.",
                ],
                "explanation": "Port address translation multiplexes many sessions onto a single public address.",
                "summary": ["PAT conserves public IPv4 space.", "Translations are tracked per flow."],
                "key_terms": ["PAT", "NAT overload", "source port", "IPv4"],
                "memory_tip": "PAT packs many hosts behind one address.",
            },
            {
                "concept": "DHCP",
                "correct": "DHCP automatically leases IP settings such as address, mask, gateway, and DNS servers.",
                "distractors": [
                    "DHCP dynamically routes packets between VLANs.",
                    "DHCP encrypts DNS lookups before forwarding.",
                    "DHCP replaces STP in switched networks.",
                ],
                "explanation": "DHCP provides centralized, automatic host configuration.",
                "summary": ["DHCP reduces manual addressing errors.", "A lease has a duration and renewal process."],
                "key_terms": ["DHCP", "lease", "gateway", "DNS"],
                "memory_tip": "DHCP delivers host parameters fast.",
            },
        ],
        "Security Fundamentals": [
            {
                "concept": "AAA",
                "correct": "AAA stands for authentication, authorization, and accounting.",
                "distractors": [
                    "AAA stands for access, analysis, and automation.",
                    "AAA stands for authentication, addressing, and auditing.",
                    "AAA stands for authorization, availability, and antivirus.",
                ],
                "explanation": "AAA controls identity verification, permissions, and activity logging.",
                "summary": ["Authenticate first, authorize next, account for actions."],
                "key_terms": ["AAA", "authentication", "authorization", "accounting"],
                "memory_tip": "Who are you, what can you do, what did you do.",
            },
            {
                "concept": "ACL",
                "correct": "An ACL filters traffic based on criteria such as source, destination, protocol, and port.",
                "distractors": [
                    "An ACL encrypts packets by default on every routed interface.",
                    "An ACL assigns VLAN IDs to incoming frames.",
                    "An ACL replaces routing tables for next-hop selection.",
                ],
                "explanation": "Access control lists permit or deny traffic based on matching rules.",
                "summary": ["ACL order matters.", "Implicit deny applies unless traffic is explicitly permitted."],
                "key_terms": ["ACL", "permit", "deny", "implicit deny"],
                "memory_tip": "ACLs are traffic rules, not encryption.",
            },
        ],
        "Automation & Programmability": [
            {
                "concept": "controller-based networking",
                "correct": "A controller-based architecture centralizes policy and reduces device-by-device configuration drift.",
                "distractors": [
                    "A controller removes the need for IP addressing entirely.",
                    "A controller converts all switches into unmanaged hubs.",
                    "A controller eliminates the data plane from the network.",
                ],
                "explanation": "Centralized management improves consistency and programmability across the network.",
                "summary": ["Control can be centralized while forwarding stays distributed."],
                "key_terms": ["controller", "policy", "automation", "orchestration"],
                "memory_tip": "Central policy, distributed forwarding.",
            },
            {
                "concept": "REST API",
                "correct": "A REST API lets software interact with network platforms using standard HTTP methods and structured data.",
                "distractors": [
                    "A REST API is used only to assign switchport VLANs manually at the CLI.",
                    "A REST API replaces JSON with proprietary binary packets.",
                    "A REST API can operate only over serial console links.",
                ],
                "explanation": "Modern network platforms expose APIs so automation tools can read and change state.",
                "summary": ["APIs enable automation pipelines.", "JSON payloads are common in network programmability."],
                "key_terms": ["REST", "HTTP", "JSON", "API"],
                "memory_tip": "REST is how scripts talk to platforms.",
            },
        ],
    },
    "AZ-900": {
        "Cloud Concepts": [
            {
                "concept": "shared responsibility model",
                "correct": "In cloud computing, some security and management duties stay with the customer while others are handled by the provider.",
                "distractors": [
                    "The provider owns every identity and access decision inside the tenant.",
                    "The customer is responsible for the provider's physical datacenter security.",
                    "Shared responsibility applies only to on-premises virtual machines.",
                ],
                "explanation": "Cloud does not remove accountability; responsibility shifts depending on the service model.",
                "summary": ["More managed service means less infrastructure management for the customer."],
                "key_terms": ["shared responsibility", "IaaS", "PaaS", "SaaS"],
                "memory_tip": "Cloud changes ownership lines, not accountability.",
            },
            {
                "concept": "scalability vs elasticity",
                "correct": "Elasticity refers to automatically adding or removing resources to match demand.",
                "distractors": [
                    "Elasticity means moving all workloads back on-premises.",
                    "Elasticity is the same as a fixed hardware upgrade.",
                    "Elasticity prevents high availability design.",
                ],
                "explanation": "Scalability grows capacity, while elasticity dynamically matches current workload demand.",
                "summary": ["Elasticity is demand-responsive scaling."],
                "key_terms": ["elasticity", "scalability", "demand", "autoscale"],
                "memory_tip": "Elastic stretches with the load.",
            },
        ],
        "Core Azure Services": [
            {
                "concept": "Azure Virtual Machines",
                "correct": "Azure Virtual Machines provide infrastructure-as-a-service compute where the customer manages the guest OS.",
                "distractors": [
                    "Azure Virtual Machines are a SaaS identity service.",
                    "Azure Virtual Machines replace the need for virtual networking.",
                    "Azure Virtual Machines require no patching of the operating system.",
                ],
                "explanation": "VMs are classic IaaS resources and still require OS-level administration.",
                "summary": ["You manage the OS in IaaS.", "Azure manages the physical host layer."],
                "key_terms": ["Azure VM", "IaaS", "guest OS"],
                "memory_tip": "VM means more control and more admin load.",
            },
            {
                "concept": "Azure Storage",
                "correct": "Azure Storage accounts can provide blob, file, queue, and table services.",
                "distractors": [
                    "Azure Storage accounts are limited to only relational databases.",
                    "Azure Storage accounts cannot be secured with role-based access control.",
                    "Azure Storage accounts are used only for on-premises backup tapes.",
                ],
                "explanation": "Storage accounts are a foundational Azure service covering multiple storage types.",
                "summary": ["Blob is object storage.", "Files can support SMB-based shares."],
                "key_terms": ["Storage account", "blob", "file", "queue", "table"],
                "memory_tip": "One account, several storage patterns.",
            },
        ],
        "Azure Management & Governance": [
            {
                "concept": "Azure Policy",
                "correct": "Azure Policy enforces and audits resource compliance against organizational rules.",
                "distractors": [
                    "Azure Policy replaces Azure subscriptions.",
                    "Azure Policy creates virtual machines from templates.",
                    "Azure Policy is used only to store application secrets.",
                ],
                "explanation": "Policy helps standardize and govern Azure resources at scale.",
                "summary": ["Policy evaluates compliance continuously.", "Initiatives group multiple policies."],
                "key_terms": ["Azure Policy", "compliance", "initiative", "governance"],
                "memory_tip": "Policy is the rulebook for the tenant.",
            },
            {
                "concept": "management groups",
                "correct": "Management groups let administrators apply governance controls above the subscription level.",
                "distractors": [
                    "Management groups are used only to assign IP addresses to VMs.",
                    "Management groups replace resource groups inside a subscription.",
                    "Management groups store application logs for Azure Monitor.",
                ],
                "explanation": "They create hierarchy so policy and RBAC can scale across subscriptions.",
                "summary": ["Hierarchy matters when governance spans many subscriptions."],
                "key_terms": ["management group", "subscription", "RBAC", "hierarchy"],
                "memory_tip": "Governance starts above subscriptions.",
            },
        ],
        "Identity & Security": [
            {
                "concept": "Microsoft Entra ID",
                "correct": "Microsoft Entra ID provides identity, authentication, and access control services for Azure and Microsoft 365.",
                "distractors": [
                    "Microsoft Entra ID is Azure's primary object storage service.",
                    "Microsoft Entra ID replaces all virtual networking features.",
                    "Microsoft Entra ID exists only for physical server monitoring.",
                ],
                "explanation": "Entra ID is the cloud identity plane for users, apps, and devices.",
                "summary": ["Identity is central to cloud security."],
                "key_terms": ["Entra ID", "identity", "authentication", "conditional access"],
                "memory_tip": "Entra is the front door for access.",
            },
            {
                "concept": "defense in depth",
                "correct": "Defense in depth uses multiple layers of security controls so one failure does not fully expose the environment.",
                "distractors": [
                    "Defense in depth means relying on a single strong perimeter firewall.",
                    "Defense in depth applies only to physical building locks.",
                    "Defense in depth removes the need for identity controls.",
                ],
                "explanation": "Layered security reduces the impact of any one broken control.",
                "summary": ["Security should overlap instead of depending on one checkpoint."],
                "key_terms": ["defense in depth", "layers", "identity", "network", "data"],
                "memory_tip": "One wall is weak. Layers buy time.",
            },
        ],
    },
    "AZ-800": {
        "Hybrid Identity": [
            {
                "concept": "directory synchronization",
                "correct": "Hybrid identity commonly syncs on-premises Active Directory identities into Microsoft Entra ID.",
                "distractors": [
                    "Hybrid identity requires replacing all on-premises user accounts immediately.",
                    "Directory sync disables single sign-on scenarios.",
                    "Hybrid identity means Azure manages only physical cabling.",
                ],
                "explanation": "Synchronization bridges legacy identity infrastructure with cloud identity services.",
                "summary": ["Hybrid identity reduces duplicate account management."],
                "key_terms": ["hybrid identity", "sync", "AD DS", "Entra ID"],
                "memory_tip": "One identity, multiple control planes.",
            },
            {
                "concept": "federation",
                "correct": "Federation allows trust-based authentication between identity systems without duplicating credentials everywhere.",
                "distractors": [
                    "Federation stores every password in clear text for compatibility.",
                    "Federation replaces group policy processing.",
                    "Federation is used only for local file permissions.",
                ],
                "explanation": "Federation extends trust boundaries for authentication workflows.",
                "summary": ["Trust relationships matter in hybrid auth design."],
                "key_terms": ["federation", "trust", "authentication"],
                "memory_tip": "Federation lets trusted systems vouch for users.",
            },
        ],
        "Windows Server Administration": [
            {
                "concept": "PowerShell remoting",
                "correct": "PowerShell remoting enables remote administration of Windows servers over management protocols such as WinRM.",
                "distractors": [
                    "PowerShell remoting is used only for DNS recursive queries.",
                    "PowerShell remoting replaces Active Directory domain trusts.",
                    "PowerShell remoting is limited to local-only sessions.",
                ],
                "explanation": "Remote administration is a core operational feature for Windows Server environments.",
                "summary": ["Automated administration scales better than RDP-only workflows."],
                "key_terms": ["PowerShell", "WinRM", "remote administration"],
                "memory_tip": "Admin at scale means scriptable remote control.",
            },
            {
                "concept": "server roles",
                "correct": "Windows Server roles install and configure major platform capabilities such as DNS, DHCP, or Hyper-V.",
                "distractors": [
                    "Server roles are used only for antivirus signature updates.",
                    "Server roles define Azure subscription billing.",
                    "Server roles are identical to endpoint user profiles.",
                ],
                "explanation": "Roles package core server functionality into manageable units.",
                "summary": ["Roles define what a server does in the environment."],
                "key_terms": ["roles", "features", "DNS", "DHCP", "Hyper-V"],
                "memory_tip": "Role equals server job.",
            },
        ],
        "Active Directory": [
            {
                "concept": "organizational units",
                "correct": "Organizational units help delegate administration and target Group Policy within Active Directory.",
                "distractors": [
                    "Organizational units replace domain controllers in every forest.",
                    "Organizational units are required to route IP traffic.",
                    "Organizational units store physical disk redundancy settings.",
                ],
                "explanation": "OUs provide logical structure for administrative scope and policy targeting.",
                "summary": ["OUs support clean delegation and policy application."],
                "key_terms": ["OU", "delegation", "Group Policy", "Active Directory"],
                "memory_tip": "OUs organize control, not authentication boundaries.",
            },
            {
                "concept": "Group Policy",
                "correct": "Group Policy applies centralized configuration settings to users and computers in Active Directory.",
                "distractors": [
                    "Group Policy is the default mechanism for Azure billing reports.",
                    "Group Policy can only be enforced on Linux hosts.",
                    "Group Policy encrypts every file share by itself.",
                ],
                "explanation": "GPOs are a primary control plane for Windows configuration management.",
                "summary": ["GPOs standardize desktop and server behavior."],
                "key_terms": ["GPO", "policy", "user settings", "computer settings"],
                "memory_tip": "GPOs push standards at scale.",
            },
        ],
        "File & Storage": [
            {
                "concept": "NTFS permissions",
                "correct": "NTFS permissions control access to files and folders on Windows volumes.",
                "distractors": [
                    "NTFS permissions assign IPv6 prefixes to subnets.",
                    "NTFS permissions create domain trusts between forests.",
                    "NTFS permissions are used only on network switches.",
                ],
                "explanation": "NTFS permissions are a core part of data access control on Windows servers.",
                "summary": ["File security is layered with share and NTFS permissions."],
                "key_terms": ["NTFS", "ACL", "permissions", "inheritance"],
                "memory_tip": "Share gets you in; NTFS decides what you touch.",
            },
            {
                "concept": "Storage Spaces",
                "correct": "Storage Spaces pools disks and can provide resiliency options such as mirroring or parity.",
                "distractors": [
                    "Storage Spaces is used only to publish websites over HTTP.",
                    "Storage Spaces manages Entra ID tenants.",
                    "Storage Spaces replaces all backup requirements.",
                ],
                "explanation": "It abstracts physical disks into resilient storage pools.",
                "summary": ["Pooling simplifies growth and resiliency design."],
                "key_terms": ["Storage Spaces", "pool", "mirror", "parity"],
                "memory_tip": "Pool first, then shape the resiliency.",
            },
        ],
        "Networking": [
            {
                "concept": "DNS zones",
                "correct": "A DNS zone stores records that map hostnames to other data such as IP addresses.",
                "distractors": [
                    "A DNS zone replaces Active Directory authentication entirely.",
                    "A DNS zone encrypts SMB traffic automatically.",
                    "A DNS zone assigns file system permissions to folders.",
                ],
                "explanation": "Windows Server commonly hosts DNS to support name resolution and AD operations.",
                "summary": ["AD depends heavily on healthy DNS."],
                "key_terms": ["DNS", "zone", "record", "name resolution"],
                "memory_tip": "If names fail, everything feels broken.",
            },
            {
                "concept": "DHCP scope",
                "correct": "A DHCP scope defines the address range and options that can be leased to clients.",
                "distractors": [
                    "A DHCP scope controls only antivirus quarantine actions.",
                    "A DHCP scope is used for password hashing policy.",
                    "A DHCP scope creates Hyper-V virtual switches.",
                ],
                "explanation": "Scopes are the heart of a DHCP deployment.",
                "summary": ["Range, exclusions, reservations, and options all matter."],
                "key_terms": ["DHCP", "scope", "lease", "reservation"],
                "memory_tip": "Scope defines who can get what address.",
            },
        ],
        "Security": [
            {
                "concept": "least privilege",
                "correct": "Least privilege means granting only the access needed for the task and no more.",
                "distractors": [
                    "Least privilege requires every admin to use Domain Admin for convenience.",
                    "Least privilege removes the need for logging.",
                    "Least privilege means every share is read-only for all users.",
                ],
                "explanation": "Restricting permissions reduces blast radius when credentials are abused.",
                "summary": ["Smaller permissions mean smaller failures."],
                "key_terms": ["least privilege", "access control", "blast radius"],
                "memory_tip": "Enough access, not maximum access.",
            },
            {
                "concept": "BitLocker",
                "correct": "BitLocker protects data at rest by encrypting Windows volumes.",
                "distractors": [
                    "BitLocker is used to route packets between VLANs.",
                    "BitLocker replaces DNS for secure name resolution.",
                    "BitLocker is only an email spam filter.",
                ],
                "explanation": "Drive encryption helps protect data if hardware is lost or stolen.",
                "summary": ["BitLocker is a data-at-rest control, not a network control."],
                "key_terms": ["BitLocker", "encryption", "TPM", "data at rest"],
                "memory_tip": "Disk gone does not mean data gone.",
            },
        ],
        "Monitoring & Recovery": [
            {
                "concept": "Windows Server Backup",
                "correct": "Backups support recovery objectives by enabling restoration after corruption, deletion, or failure.",
                "distractors": [
                    "Backups remove the need for monitoring entirely.",
                    "Backups permanently prevent ransomware from encrypting data.",
                    "Backups are used only to apply Group Policy.",
                ],
                "explanation": "Recovery planning depends on tested, trustworthy backups.",
                "summary": ["A backup strategy matters only if restores are tested."],
                "key_terms": ["backup", "restore", "recovery", "RPO", "RTO"],
                "memory_tip": "Unverified backup is a theory, not a plan.",
            },
            {
                "concept": "event monitoring",
                "correct": "Monitoring event logs helps administrators detect faults, service failures, and suspicious activity.",
                "distractors": [
                    "Event logs are used only to assign DHCP addresses.",
                    "Event monitoring replaces patch management.",
                    "Event logs cannot support troubleshooting.",
                ],
                "explanation": "Event visibility is a baseline operational and security requirement.",
                "summary": ["Logs help both troubleshooting and detection."],
                "key_terms": ["logs", "Event Viewer", "monitoring", "alerts"],
                "memory_tip": "If you do not watch signals, you miss the failure curve.",
            },
        ],
    },
    "Security+": {
        "General Security Concepts": [
            {
                "concept": "CIA triad",
                "correct": "The CIA triad stands for confidentiality, integrity, and availability.",
                "distractors": [
                    "The CIA triad stands for control, inspection, and access.",
                    "The CIA triad stands for confidentiality, identity, and audit.",
                    "The CIA triad stands for cyber, infrastructure, and assurance.",
                ],
                "explanation": "These three principles anchor many security decisions and tradeoffs.",
                "summary": ["Confidentiality restricts exposure.", "Integrity protects trust in data.", "Availability keeps services usable."],
                "key_terms": ["CIA triad", "confidentiality", "integrity", "availability"],
                "memory_tip": "Keep it secret, accurate, and reachable.",
            },
            {
                "concept": "zero trust",
                "correct": "Zero trust assumes no user or device should be trusted implicitly, even inside the network perimeter.",
                "distractors": [
                    "Zero trust means disabling all multifactor authentication.",
                    "Zero trust applies only to consumer wireless networks.",
                    "Zero trust requires a flat network to simplify access.",
                ],
                "explanation": "Verification should be continuous and contextual, not based on location alone.",
                "summary": ["Trust is earned continuously, not granted permanently."],
                "key_terms": ["zero trust", "verification", "context", "least privilege"],
                "memory_tip": "Inside the network does not equal safe.",
            },
        ],
        "Threats & Vulnerabilities": [
            {
                "concept": "phishing",
                "correct": "Phishing uses deceptive messages to trick users into revealing credentials or performing risky actions.",
                "distractors": [
                    "Phishing is a disk redundancy technology.",
                    "Phishing is a process that automatically patches servers.",
                    "Phishing only affects legacy analog phone systems.",
                ],
                "explanation": "Social engineering attacks target human decision-making, not just technical flaws.",
                "summary": ["Humans are often the initial access path."],
                "key_terms": ["phishing", "social engineering", "credential theft"],
                "memory_tip": "If urgency spikes and context is thin, slow down.",
            },
            {
                "concept": "vulnerability management",
                "correct": "Vulnerability management is the ongoing process of identifying, prioritizing, and remediating weaknesses.",
                "distractors": [
                    "Vulnerability management is a one-time annual password reset.",
                    "Vulnerability management means accepting every finding without prioritization.",
                    "Vulnerability management replaces backup planning.",
                ],
                "explanation": "Security teams need repeatable workflows for scanning, validating, and fixing risk.",
                "summary": ["Discovery without prioritization creates noise."],
                "key_terms": ["vulnerability", "scan", "prioritize", "remediation"],
                "memory_tip": "Find, rank, fix, verify.",
            },
        ],
        "Security Architecture": [
            {
                "concept": "segmentation",
                "correct": "Network segmentation limits lateral movement by separating systems into controlled zones.",
                "distractors": [
                    "Segmentation guarantees perfect endpoint antivirus coverage.",
                    "Segmentation means all devices share one unrestricted VLAN.",
                    "Segmentation is used only for physical office seating plans.",
                ],
                "explanation": "Segmentation reduces attack spread and sharpens control boundaries.",
                "summary": ["Smaller trust zones reduce blast radius."],
                "key_terms": ["segmentation", "lateral movement", "zones", "blast radius"],
                "memory_tip": "Walls inside the network matter.",
            },
            {
                "concept": "multifactor authentication",
                "correct": "MFA strengthens access control by requiring more than one factor type during authentication.",
                "distractors": [
                    "MFA means using the same password twice.",
                    "MFA is only a backup technology for file systems.",
                    "MFA replaces authorization policies after login.",
                ],
                "explanation": "Combining factors makes stolen credentials less useful on their own.",
                "summary": ["Different factor categories matter more than more of the same factor."],
                "key_terms": ["MFA", "authentication", "factor", "access control"],
                "memory_tip": "One stolen secret should not open the door.",
            },
        ],
        "Security Operations": [
            {
                "concept": "incident response",
                "correct": "Incident response includes preparation, detection, containment, eradication, recovery, and lessons learned.",
                "distractors": [
                    "Incident response begins only after legal action is complete.",
                    "Incident response is limited to antivirus deployment.",
                    "Incident response ends before recovery starts.",
                ],
                "explanation": "A disciplined lifecycle keeps teams organized when pressure is high.",
                "summary": ["Contain first, recover cleanly, then improve the process."],
                "key_terms": ["incident response", "containment", "eradication", "recovery"],
                "memory_tip": "Pressure exposes weak process. Train before the hit.",
            },
            {
                "concept": "logging and monitoring",
                "correct": "Security monitoring depends on collecting and reviewing logs from critical systems and identity sources.",
                "distractors": [
                    "Logs are useful only for capacity planning.",
                    "Monitoring removes the need for alert tuning.",
                    "Logs are irrelevant once MFA is enabled.",
                ],
                "explanation": "Detection requires visibility, and visibility starts with useful telemetry.",
                "summary": ["No logs means weak detection and weak forensics."],
                "key_terms": ["logs", "SIEM", "monitoring", "telemetry"],
                "memory_tip": "You cannot defend what you cannot see.",
            },
        ],
        "Governance & Risk": [
            {
                "concept": "risk assessment",
                "correct": "Risk assessment evaluates threats, vulnerabilities, likelihood, and impact to prioritize treatment.",
                "distractors": [
                    "Risk assessment is only a finance department process.",
                    "Risk assessment eliminates the need for security controls.",
                    "Risk assessment means patching systems without reviewing business impact.",
                ],
                "explanation": "Organizations should invest where risk is real, not where noise is loud.",
                "summary": ["Impact and likelihood drive prioritization."],
                "key_terms": ["risk", "likelihood", "impact", "treatment"],
                "memory_tip": "Not every vulnerability is equal risk.",
            },
            {
                "concept": "policies and procedures",
                "correct": "Security policies define intent, while procedures describe the repeatable steps to carry it out.",
                "distractors": [
                    "Policies are temporary logs of firewall traffic.",
                    "Procedures replace all regulatory requirements.",
                    "Policies are only for software development teams.",
                ],
                "explanation": "Governance fails when teams know the rule but not the execution path.",
                "summary": ["Policy sets direction. Procedure drives execution."],
                "key_terms": ["policy", "procedure", "governance", "standard"],
                "memory_tip": "Direction without process stays theoretical.",
            },
        ],
    },
    "Network+": {
        "Networking Concepts": [
            {
                "concept": "subnetting",
                "correct": "Subnetting divides an IP network into smaller logical segments for control and address efficiency.",
                "distractors": [
                    "Subnetting encrypts packets before they leave the NIC.",
                    "Subnetting replaces DNS records for hostnames.",
                    "Subnetting is used only for wireless authentication.",
                ],
                "explanation": "Subnetting supports cleaner routing, security boundaries, and address planning.",
                "summary": ["Smaller subnets help contain broadcasts and organize space."],
                "key_terms": ["subnet", "prefix", "broadcast", "routing"],
                "memory_tip": "Subnetting shapes the map before traffic hits it.",
            },
            {
                "concept": "TCP vs UDP",
                "correct": "TCP is connection-oriented and reliable, while UDP is connectionless with lower overhead.",
                "distractors": [
                    "TCP is connectionless and used only for streaming video.",
                    "UDP guarantees ordered delivery with acknowledgments.",
                    "TCP and UDP operate at the Data Link layer.",
                ],
                "explanation": "Transport choice depends on whether reliability or speed and simplicity matter more.",
                "summary": ["TCP buys reliability. UDP buys speed and lower overhead."],
                "key_terms": ["TCP", "UDP", "transport", "reliability"],
                "memory_tip": "TCP talks first. UDP just sends.",
            },
        ],
        "Network Implementation": [
            {
                "concept": "wireless standards",
                "correct": "Wireless standards define operating characteristics such as frequency bands, throughput, and channel use.",
                "distractors": [
                    "Wireless standards assign NTFS permissions to files.",
                    "Wireless standards are used only for serial cabling pinouts.",
                    "Wireless standards replace IP addressing requirements.",
                ],
                "explanation": "Implementation work often depends on understanding the practical limits of Wi-Fi standards.",
                "summary": ["Band selection affects coverage and interference."],
                "key_terms": ["802.11", "frequency", "channel", "throughput"],
                "memory_tip": "Radio design is tradeoffs, not magic.",
            },
            {
                "concept": "switching infrastructure",
                "correct": "Switches forward frames based on MAC address learning within a Layer 2 domain.",
                "distractors": [
                    "Switches route packets across the internet using DNS zones.",
                    "Switches translate URLs into IP addresses.",
                    "Switches are designed only for disk mirroring.",
                ],
                "explanation": "Layer 2 switching behavior is fundamental to access network implementation.",
                "summary": ["Switches learn source MACs and forward toward known destinations."],
                "key_terms": ["switch", "MAC table", "forwarding", "Layer 2"],
                "memory_tip": "Switches learn from the source and decide on the destination.",
            },
        ],
        "Network Operations": [
            {
                "concept": "documentation",
                "correct": "Accurate network documentation speeds troubleshooting, change control, and recovery.",
                "distractors": [
                    "Documentation eliminates the need for backups.",
                    "Documentation is useful only for audits, not operations.",
                    "Documentation replaces monitoring tools entirely.",
                ],
                "explanation": "Operational discipline depends on reliable diagrams, inventories, and runbooks.",
                "summary": ["If the map is wrong, troubleshooting gets slower and riskier."],
                "key_terms": ["documentation", "runbook", "inventory", "diagram"],
                "memory_tip": "Good notes save time under pressure.",
            },
            {
                "concept": "high availability",
                "correct": "High availability uses redundancy and failover design to keep services online during faults.",
                "distractors": [
                    "High availability guarantees zero-cost infrastructure.",
                    "High availability means using a single device with maximum utilization.",
                    "High availability removes the need for monitoring.",
                ],
                "explanation": "Operational resilience requires redundancy, testing, and clear failover behavior.",
                "summary": ["Redundancy is useful only if failover actually works."],
                "key_terms": ["HA", "redundancy", "failover", "resilience"],
                "memory_tip": "Two devices help only if the second can carry the load.",
            },
        ],
        "Network Security": [
            {
                "concept": "firewalls",
                "correct": "Firewalls enforce traffic control rules between security zones based on policy.",
                "distractors": [
                    "Firewalls assign MAC addresses to endpoints.",
                    "Firewalls replace every need for MFA.",
                    "Firewalls are used only to increase Wi-Fi speed.",
                ],
                "explanation": "Policy-driven traffic filtering is a baseline network security function.",
                "summary": ["A firewall is only as good as the rule design and review process."],
                "key_terms": ["firewall", "policy", "ACL", "security zone"],
                "memory_tip": "Control the path, not just the endpoint.",
            },
            {
                "concept": "VPN",
                "correct": "A VPN creates an encrypted tunnel across an untrusted network to protect data in transit.",
                "distractors": [
                    "A VPN is only a storage redundancy mechanism.",
                    "A VPN assigns DHCP scopes to every branch office.",
                    "A VPN guarantees endpoint devices are malware-free.",
                ],
                "explanation": "VPNs help preserve confidentiality and integrity across public or shared paths.",
                "summary": ["Tunneling protects transport, not endpoint hygiene."],
                "key_terms": ["VPN", "tunnel", "encryption", "data in transit"],
                "memory_tip": "Secure tunnel, still need secure endpoints.",
            },
        ],
        "Troubleshooting": [
            {
                "concept": "layered troubleshooting",
                "correct": "A layered troubleshooting approach isolates faults systematically instead of guessing.",
                "distractors": [
                    "Layered troubleshooting means changing multiple variables at once.",
                    "Layered troubleshooting ignores physical connectivity issues.",
                    "Layered troubleshooting is used only for software licensing.",
                ],
                "explanation": "Methodical isolation reduces downtime and avoids self-inflicted mistakes.",
                "summary": ["Check basics first, then move upward through the stack."],
                "key_terms": ["troubleshooting", "OSI", "isolation", "methodology"],
                "memory_tip": "Discipline beats panic in outage work.",
            },
            {
                "concept": "baseline comparison",
                "correct": "Comparing current behavior to a known-good baseline helps identify abnormal performance and faults.",
                "distractors": [
                    "Baseline comparison replaces the need for packet captures.",
                    "Baseline comparison is relevant only to accounting records.",
                    "Baseline comparison works only after a full hardware refresh.",
                ],
                "explanation": "You notice drift faster when you know what normal actually looks like.",
                "summary": ["Baselines make anomalies measurable."],
                "key_terms": ["baseline", "normal behavior", "performance", "drift"],
                "memory_tip": "No baseline means every problem feels subjective.",
            },
        ],
    },
}


def _generated_fact(exam: str, domain: str, focus: str) -> dict:
    provider = catalog_provider(exam)
    concept = focus
    return {
        "concept": concept,
        "correct": f"In {exam}, {concept} focuses on applying {domain.lower()} principles in a way that improves reliability, security, and operational clarity.",
        "distractors": [
            f"In {exam}, {concept} is used only for ignoring governance and validation requirements.",
            f"In {exam}, {concept} removes the need for documentation, testing, or verification.",
            f"In {exam}, {concept} applies only to isolated theory and has no operational impact.",
        ],
        "explanation": f"{provider} certification objectives for {exam} expect candidates to connect {concept.lower()} with practical decisions inside {domain}.",
        "summary": [
            f"{concept} is part of the {domain} skill set.",
            f"Strong answers connect {concept.lower()} to real implementation or operational outcomes.",
        ],
        "key_terms": [concept, domain, exam, provider],
        "memory_tip": f"Treat {concept.lower()} as something you must be able to explain, apply, and verify.",
    }


def _generated_question_bank() -> dict:
    generated = {}
    for exam, blueprint in CERT_BLUEPRINTS.items():
        if exam in QUESTION_BANK:
            continue
        generated[exam] = {}
        for domain in blueprint["domains"]:
            generated[exam][domain] = [
                _generated_fact(exam, domain, f"{domain} fundamentals"),
                _generated_fact(exam, domain, f"{domain} implementation"),
                _generated_fact(exam, domain, f"{domain} troubleshooting"),
            ]
    return generated


def _merge_question_banks(base: dict, extra: dict) -> dict:
    merged = {}
    for exam, domains in base.items():
        merged[exam] = {}
        for domain, facts in domains.items():
            merged[exam][domain] = [*facts, *extra.get(exam, {}).get(domain, [])]
    return merged


QUESTION_BANK = _merge_question_banks(QUESTION_BANK, EXTRA_QUESTION_BANK)
QUESTION_BANK.update(_generated_question_bank())


def get_question_pool(exam: str, domains: list[str] | None = None) -> list[dict]:
    selected_domains = domains or EXAM_DOMAINS[exam]
    items = []
    for domain in selected_domains:
        for fact in QUESTION_BANK[exam][domain]:
            item = fact.copy()
            item["exam"] = exam
            item["domain"] = domain
            items.append(item)
    return items


def list_topics_for_exam(exam: str) -> list[str]:
    topics = []
    for domain in EXAM_DOMAINS[exam]:
        for fact in QUESTION_BANK[exam][domain]:
            topics.append(fact["concept"])
    return sorted(set(topics))


def get_cheat_sheet(exam: str, topic: str) -> dict:
    grouped = defaultdict(list)
    for domain in EXAM_DOMAINS[exam]:
        for fact in QUESTION_BANK[exam][domain]:
            grouped[fact["concept"]].append(fact)

    items = grouped.get(topic, [])
    if not items:
        return {
            "summary": ["No cheat sheet available yet."],
            "key_terms": [],
            "memory_tips": [],
            "watch_outs": [],
            "why_it_matters": "This topic has not been expanded into a local cheat sheet yet.",
        }

    summary = []
    key_terms = set()
    memory_tips = []
    watch_outs = []
    why_it_matters = []
    for item in items:
        summary.extend(item["summary"])
        key_terms.update(item["key_terms"])
        memory_tips.append(item["memory_tip"])
        watch_outs.extend(item["distractors"][:2])
        why_it_matters.append(item["explanation"])
    return {
        "summary": list(dict.fromkeys(summary))[:6],
        "key_terms": sorted(key_terms),
        "memory_tips": list(dict.fromkeys(memory_tips))[:4],
        "watch_outs": list(dict.fromkeys(watch_outs))[:4],
        "why_it_matters": list(dict.fromkeys(why_it_matters))[0],
    }
