# J_AI Evaluation Report

Course: ITE 402 | Provider: OllamaProvider:qwen3.8:27b:think=low | Generated: 2026-10-12 10:24

## Scoreboard

| Metric | Value |
|---|---|
| cases total | 5 |
| cases graded | 5 |
| cases guard rejected | 0 |
| cases provider error | 0 |
| cases bad score value | 0 |
| average score | 1.4 |
| pass rate | 0.0 |
| avg model latency seconds | 68.57 |
| average: requirements_analysis | 2.0 |
| average: logical_design | 1.0 |
| average: protocol_selection | 1.0 |
| average: security_strategy | 1.0 |

## REQ_001 | requirements_analysis | 3/10 FAIL (graded)

**Question:** A small clinic has 1 main site and 1 remote branch. They need reliable internet access, secure patient record access, and minimal downtime. Budget is limited. They expect growth from 30 to 80 staff within 2 years.

**Answer:**

> A clinic with a main and a branch and 30 staff, so first the clinic needs good internet, maybe 200mbp at the main and 100mbp at the branch, and a computer for every doctor and receptionist. The records should be on a system both sites can open so the patient doesn't have to repeat everything if they go to the other one. If the internet goes down they could use mobile data from a phone until it comes back. When they hire more people they can just buy more computers.

**Missing Points:**
- constraints
- security

**Technical Errors:**
- Suggesting mobile data from a phone as a failover for a clinic handling patient records is not a viable or secure continuity solution ("they could use mobile data from a phone until it comes back")
- Treating growth as simply purchasing more computers ignores network capacity, server scalability, licensing, and infrastructure planning ("they can just buy more computers")

**Strengths:**
- Identified the need for a shared records system accessible from both sites
- Specified bandwidth for both the main site and branch
- Acknowledged future growth, even if superficially

## REQ_002 | requirements_analysis | 1/10 FAIL (graded)

**Question:** A university building has 6 labs and 12 classrooms. Each lab has 35 PCs. WiFi must cover classrooms. Some devices are IoT sensors. The network must support online exams without drops. IT staff is small.

**Answer:**

> A university building that has 6 labs with 35 PCs each and 12 classrooms, so 210 PCs in the labs, each lab should have a teacher PC and a printer too. The classrooms need a projector and a smart board each and the teacher connects the laptop to it. For the online exams the students should close all other programs and the teacher watches them so nobody cheats. The IT staff is small so they should hire 1 or 2 more people to help.

**Missing Points:**
- traffic types
- availability
- wireless coverage
- segmentation

**Technical Errors:**
- Treating cheating prevention as a network design solution: 'the students should close all other programs and the teacher watches them so nobody cheats'

**Strengths:**
- Acknowledged the small IT staff constraint and proposed a mitigation (hiring)
- Correctly calculated total lab PCs (6 × 35 = 210)

## LOG_001 | logical_design | 1/10 FAIL (graded)

**Question:** A mid size company has 3 departments: HR, Finance, Engineering. Engineering has heavy internal traffic and needs lab isolation. Finance needs strict access control. Provide a logical design approach.

**Answer:**

> A company with 3 departments HR, Finance and Engineering, so each one should have their own room and their own shared folder on the server. Engineering works with big files so they need faster computers and a bigger hard drive on the server. Finance has sensitive data so only Finance people get the password to the Finance folder, and the manager approves who gets added. HR keeps the employees files and does the hiring so they mostly need email and the HR system.

**Missing Points:**
- hierarchical design
- segmentation
- addressing plan
- routing approach
- redundancy

**Design Flaws:**
- Confuses physical separation with logical network segmentation: 'each one should have their own room'
- Proposes a single shared password as an access control mechanism rather than proper authentication/authorization: 'only Finance people get the password to the Finance folder'
- Focuses on hardware sizing (computers, hard drives) rather than any network design element: 'they need faster computers and a bigger hard drive on the server'
- No mention of VLANs, subnets, ACLs, routing, or any logical network construct

**Strengths:**
- Attempts to differentiate departmental needs (Engineering heavy traffic, Finance sensitive data, HR administrative)
- Recognizes that Finance requires restricted access, even though the proposed mechanism is incorrect

## PROT_001 | protocol_selection | 1/10 FAIL (graded)

**Question:** Choose a routing protocol for a campus network with multiple buildings and future growth. Justify your choice briefly.

**Answer:**

> A campus with multiple buildings, so I'd go with RIP because it's simple to set up and the IT staff won't need much training, you just enable it on the routers and they share their routes with each other automatically. If the campus grows they can add more routers and turn RIP on there too.

**Incorrect Claims:**
- RIP is suitable for a campus with multiple buildings and future growth — RIP has a maximum hop count of 15 and slow convergence, making it unsuitable for multi-building campus networks with growth plans ('If the campus grows they can add more routers and turn RIP on there too')

**Missing Reasoning:**
- No mention of OSPF or link-state routing as a more appropriate choice
- No mention of EIGRP or fast convergence as a requirement for the scenario
- No proper discussion of scalability limitations (RIP hop count cap of 15, slow convergence under load)
- No comparison of RIP against more suitable protocols for the given scenario

**Strengths:**
- Made a substantive attempt at justifying a protocol choice
- Acknowledged the growth requirement, even if the conclusion was incorrect

## SEC_001 | security_strategy | 1/10 FAIL (graded)

**Question:** A company allows remote work. They host internal apps and a public website. Propose security strategies for internal and perimeter security.

**Answer:**

> A company with remote work and a website, so everyone should have antivirus on their laptop and keep it updated. The remote workers should not use public WiFi in cafes. Passwords should be changed every month and written somewhere safe. The website should be backed up every week in case it gets hacked so they can restore it.

**Missing Controls:**
- segmentation
- least privilege
- remote access protection (no VPN, MFA, or technical remote access controls mentioned)
- monitoring
- public facing isolation (no DMZ, WAF, or separation of public website from internal systems)

**Risk Gaps:**
- No network segmentation between internal apps and public website
- No mention of VPN or MFA for remote access
- No monitoring, logging, or alerting strategy
- No isolation of the public-facing website from internal infrastructure
- No least privilege or access control model

**Strengths:**
- Acknowledges the remote work context and attempts to address it
- Mentions endpoint antivirus as a basic hygiene measure
- Considers backup/recovery for the website

