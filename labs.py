from __future__ import annotations

from cert_catalog import CERT_BLUEPRINTS, catalog_provider

HOME_LABS = {
    "CCNA": [
        {
            "id": "ccna-routed-campus",
            "title": "Build A Small Routed Campus",
            "why": "This lab turns VLANs, trunking, inter-VLAN routing, DHCP, and ACL concepts into one realistic topology.",
            "steps": [
                "Create three VLANs for users, servers, and management in Packet Tracer, GNS3, or real switches.",
                "Configure 802.1Q trunk links between switches and verify VLAN propagation.",
                "Set up router-on-a-stick or Layer 3 switch SVIs for inter-VLAN routing.",
                "Add DHCP for end-user VLANs and verify clients receive valid addresses and gateways.",
                "Apply an ACL that limits user access to the management subnet while still allowing DNS and DHCP.",
                "Document the topology, addressing plan, and verification commands you used.",
            ],
            "resume_bullets": [
                "Built a multi-VLAN campus lab with inter-VLAN routing, DHCP, and ACL-based segmentation using Cisco-style configurations.",
                "Validated Layer 2 and Layer 3 connectivity with trunking, gateway design, and access-control testing in a simulated enterprise topology.",
            ],
        },
        {
            "id": "ccna-config-drift",
            "title": "Automate Config Backup And Drift Checks",
            "why": "This lab connects CCNA automation topics to an actual repeatable workflow.",
            "steps": [
                "Create two or more lab devices or simulated nodes with saved configurations.",
                "Write a small script that pulls config output over SSH or uses a mocked API response if direct device access is unavailable.",
                "Store the configs in versioned local files and compare them against a known-good baseline.",
                "Flag differences such as missing VLANs, changed IP addresses, or removed ACL entries.",
                "Update the script to print a short compliance summary at the end.",
                "Save the script and a sample drift report in your study notes folder.",
            ],
            "resume_bullets": [
                "Created a local network automation workflow to back up device configurations and detect configuration drift against a baseline.",
                "Used scripting and validation logic to improve repeatability for network change review and recovery tasks.",
            ],
        },
    ],
    "AZ-900": [
        {
            "id": "az900-core-services-map",
            "title": "Map Core Azure Services In A Sandbox",
            "why": "This lab helps tie abstract Azure service names to how they fit together in a basic cloud environment.",
            "steps": [
                "Create a free or sandbox Azure tenant if available, or use architecture diagrams if you do not want to deploy resources.",
                "Sketch a simple environment with a resource group, virtual network, storage account, and virtual machine.",
                "Identify which services are IaaS, which are platform services, and which are governance services.",
                "Add tags and a naming standard to the design so governance concepts appear in the lab.",
                "Explain where shared responsibility changes between the VM, storage, and identity layers.",
                "Write a one-page summary of cost, management, and security tradeoffs.",
            ],
            "resume_bullets": [
                "Designed and documented a foundational Azure lab covering resource groups, virtual networking, storage, and identity/governance concepts.",
                "Mapped cloud service choices to shared responsibility, cost model, and operational controls in a structured Azure study environment.",
            ],
        },
        {
            "id": "az900-governance-identity",
            "title": "Governance And Identity Walkthrough",
            "why": "AZ-900 often tests governance and identity language that feels vague until you apply it.",
            "steps": [
                "Create a sample hierarchy with a management group, subscription, resource group, and a few tagged resources.",
                "Define two role-based access control scenarios for an admin and a read-only auditor.",
                "Write one Azure Policy rule you would enforce, such as required tags or allowed regions.",
                "Describe how Microsoft Entra ID supports sign-in and conditional access in this environment.",
                "Summarize where governance is enforced and where workloads are still customer-managed.",
                "Turn the output into a short architecture note or portfolio artifact.",
            ],
            "resume_bullets": [
                "Documented Azure governance and identity controls using RBAC, policy, resource hierarchy, and Entra ID access scenarios.",
                "Translated cloud governance requirements into practical administrative and security design decisions for a sandbox tenant.",
            ],
        },
    ],
    "AZ-800": [
        {
            "id": "az800-hybrid-identity",
            "title": "Hybrid Identity Mini Lab",
            "why": "This lab gives hands-on context for sync, SSO, and directory-management topics.",
            "steps": [
                "Stand up a Windows Server VM or diagram a notional environment if local virtualization is limited.",
                "Model an on-premises Active Directory domain with users, groups, and organizational units.",
                "Define how identities would sync to Microsoft Entra ID and where SSO would be applied.",
                "Create a Group Policy example for a workstation baseline and explain how it would be linked.",
                "Document administrative roles, least-privilege boundaries, and recovery considerations.",
                "Capture screenshots or architecture notes to show the workflow end to end.",
            ],
            "resume_bullets": [
                "Built a hybrid identity lab using Active Directory concepts, organizational units, Group Policy, and planned Entra ID synchronization flows.",
                "Documented role delegation, policy targeting, and sign-in design across on-premises and cloud identity boundaries.",
            ],
        },
        {
            "id": "az800-operations-recovery",
            "title": "Windows Server Operations And Recovery",
            "why": "AZ-800 rewards administrators who can connect daily operations with backup and recovery planning.",
            "steps": [
                "Deploy a Windows Server VM with DNS, DHCP, or file services enabled.",
                "Configure a shared folder with both share permissions and NTFS permissions.",
                "Use PowerShell or Windows Admin Center to document service status and configuration.",
                "Define backup scope, expected RPO/RTO, and a simple restore sequence.",
                "Trigger a safe configuration change and capture a rollback plan.",
                "Write a short post-lab report on operational risk and recovery readiness.",
            ],
            "resume_bullets": [
                "Configured Windows Server services, file-share permissions, and administrative tooling while documenting rollback and recovery procedures.",
                "Linked daily server operations with backup scope, restoration planning, and least-privilege access design in a Windows lab environment.",
            ],
        },
    ],
    "Security+": [
        {
            "id": "secplus-segmented-soc",
            "title": "Segmented SOC-In-A-Box Lab",
            "why": "This lab brings together segmentation, logging, incident response, and least-privilege ideas in one project.",
            "steps": [
                "Create a small virtual lab with a workstation, a server, and a firewall or router separating zones.",
                "Place systems into separate trust zones and define the allowed communication paths between them.",
                "Enable logs on the host, firewall, or a lightweight SIEM/log collector if available.",
                "Simulate a suspicious event such as repeated failed logins or a blocked connection attempt.",
                "Walk through containment, evidence capture, and lessons learned using a short incident playbook.",
                "Write down what controls failed, what controls worked, and what would improve detection next time.",
            ],
            "resume_bullets": [
                "Built a security homelab with segmented trust zones, logging, and incident-response workflow testing for hands-on security practice.",
                "Documented detection, containment, and post-incident review steps using a repeatable playbook-driven process.",
            ],
        },
        {
            "id": "secplus-identity-hardening",
            "title": "Identity And Access Hardening Lab",
            "why": "Security+ repeatedly tests authentication, MFA, least privilege, and access-review concepts.",
            "steps": [
                "Create sample user, admin, and service accounts in a local directory or mocked identity table.",
                "Define which roles need elevated privileges and which should remain standard users.",
                "Add MFA requirements and explain where conditional access or stronger verification would apply.",
                "Review the accounts for excess permissions and remove anything that is not justified.",
                "Create a simple audit log or access-review checklist for quarterly review.",
                "Summarize how your final design reduced blast radius compared with the starting point.",
            ],
            "resume_bullets": [
                "Designed and reviewed an access-control lab with MFA, least-privilege role separation, and repeatable access-audit steps.",
                "Reduced account blast radius by identifying excess permissions and documenting a practical identity hardening workflow.",
            ],
        },
    ],
    "Network+": [
        {
            "id": "netplus-office-buildout",
            "title": "Small Office Network Buildout",
            "why": "This lab makes core Network+ topics tangible by combining addressing, switching, Wi-Fi, and operations.",
            "steps": [
                "Design a small office network with internet access, one switch, one wireless segment, and one server or service node.",
                "Create an IPv4 addressing plan, default gateway design, and basic DNS/DHCP assumptions.",
                "Document where PoE, wireless channels, and switching infrastructure choices matter.",
                "Verify local and remote connectivity, then capture baseline latency or throughput notes.",
                "Perform one controlled change and record the before-and-after results.",
                "Write an operations summary that explains how you would hand this environment to another technician.",
            ],
            "resume_bullets": [
                "Built and documented a small office network lab with addressing, switching, wireless, and baseline connectivity validation.",
                "Used structured change documentation and verification testing to support operational handoff and troubleshooting readiness.",
            ],
        },
        {
            "id": "netplus-troubleshooting-evidence",
            "title": "Troubleshooting And Evidence Lab",
            "why": "Network+ expects a methodical troubleshooting approach, not guesswork.",
            "steps": [
                "Introduce three controlled faults such as a wrong gateway, bad DNS server, and disabled switchport.",
                "Use a layered troubleshooting process to isolate each issue one at a time.",
                "Capture evidence through ping, traceroute, interface status, logs, or packet captures.",
                "Write down the symptom, root cause, fix, and verification result for each fault.",
                "Create a short baseline document showing normal-state outputs after recovery.",
                "Compare how troubleshooting changes when you have a baseline versus when you do not.",
            ],
            "resume_bullets": [
                "Ran a structured network troubleshooting lab using baseline comparison, packet-level evidence, and layered fault isolation techniques.",
                "Documented root-cause analysis and verification steps for connectivity, DNS, and switching faults in a repeatable support workflow.",
            ],
        },
    ],
}


def get_home_labs(exam: str) -> list[dict]:
    if exam in HOME_LABS:
        return HOME_LABS.get(exam, [])

    blueprint = CERT_BLUEPRINTS.get(exam)
    if not blueprint:
        return []

    provider = catalog_provider(exam)
    domain_a = blueprint["domains"][0]
    domain_b = blueprint["domains"][1] if len(blueprint["domains"]) > 1 else blueprint["domains"][0]
    exam_slug = exam.lower().replace("+", "plus").replace(" ", "-")
    return [
        {
            "id": f"{exam_slug}-core-lab",
            "title": f"{exam} Core Implementation Lab",
            "why": f"This lab converts the {domain_a} and {domain_b} objectives into applied work instead of passive reading.",
            "steps": [
                f"Review the exam objectives for {domain_a} and {domain_b} and define a small lab outcome.",
                f"Build a local sandbox, diagram, or simulated environment that exercises {domain_a}.",
                f"Add one configuration, workflow, or design decision tied directly to {domain_b}.",
                "Test the environment and record what worked, what failed, and how you corrected it.",
                "Capture evidence such as screenshots, terminal output, architecture notes, or configuration snippets.",
                "Write a short summary explaining which certification objectives this lab strengthened.",
            ],
            "resume_bullets": [
                f"Built a hands-on {provider} {exam} lab focused on {domain_a.lower()} and {domain_b.lower()}, then documented validation results and key design decisions.",
                f"Translated {exam} objectives into a working practice environment with repeatable testing, evidence capture, and written implementation notes.",
            ],
        },
        {
            "id": f"{exam_slug}-ops-lab",
            "title": f"{exam} Operations And Validation Lab",
            "why": f"This lab reinforces the operational side of {exam} by forcing verification, troubleshooting, and documentation discipline.",
            "steps": [
                f"Choose one domain from {exam} that feels weakest and define a realistic scenario around it.",
                "Implement a baseline configuration, workflow, or design and document the expected outcome.",
                "Introduce a small fault, policy gap, or misconfiguration on purpose.",
                "Use a methodical troubleshooting or validation process to identify and correct the issue.",
                "Capture proof of the fix and compare the broken and restored states.",
                "Summarize how this lab improved your confidence and what would go on a portfolio or GitHub repo.",
            ],
            "resume_bullets": [
                f"Created and validated an operations-focused {exam} lab that included controlled failure testing, troubleshooting, and recovery documentation.",
                f"Improved hands-on readiness for {exam} by pairing implementation work with verification evidence and post-lab analysis.",
            ],
        },
    ]


def lab_note_feedback(note: str) -> list[str]:
    cleaned = note.strip()
    checks = []
    if len(cleaned) < 60:
        checks.append("Use at least 60 characters.")
    lowered = cleaned.lower()
    required_prefixes = {
        "Built:": "Add a `Built:` section describing what you created.",
        "Verified:": "Add a `Verified:` section describing how you tested it.",
        "Evidence:": "Add an `Evidence:` section describing screenshots, outputs, or notes you captured.",
    }
    for prefix, message in required_prefixes.items():
        if prefix.lower() not in lowered:
            checks.append(message)
    return checks
