# J_AI Evaluation Report

Course: ITE 402 | Provider: OllamaProvider:qwen3.8:27b:think=low | Generated: 2026-09-10 19:33

## Scoreboard

| Metric | Value |
|---|---|
| cases total | 5 |
| cases graded | 3 |
| cases guard rejected | 2 |
| cases provider error | 0 |
| cases bad score value | 0 |
| average score | 1.2 |
| pass rate | 0.0 |
| avg model latency seconds | 80.92 |
| average: requirements_analysis | 2.5 |
| average: logical_design | 1.0 |
| average: protocol_selection | 0.0 |
| average: security_strategy | 0.0 |

## REQ_001 | requirements_analysis | 4/10 FAIL (graded)

**Question:** A small clinic has 1 main site and 1 remote branch. They need reliable internet access, secure patient record access, and minimal downtime. Budget is limited. They expect growth from 30 to 80 staff within 2 years.

**Answer:**

> Budget should be taken into consideration, so I have 1 main site and 1 branch, a patient records, 30 staff to begin with that would increase to 80 within 2 years. 1st build the main site and its systems, assigns staffs to their profession, since it's a clinic then it should be a focused profession, could be a dental clinic, the main probably have about 18 out of the 30 staffs, a director (could be a doctor as well), 2 doctors, 4 nurses, 2-3 ambulance car drivers on shift, 3 cleaners, 3 receptionists on shift, 2 extras (they can be nurses or assistances who could also assist on emergencies). The branch should function on regular week days of 8 hours a day. It could have 1 director (and doctor), 1 doctor, 2-3 nurses, 2 receptionist, 2 ambulance staff (driver and an assistant who could also drive in case of the main one is off). 2 cleaners, 2 extras that could either help indoors or out or on-behalf. Each branch should hold space for expansion in case of scaling up to 80 for what is expected in 2 years. Both clinics should be able to communicate with each other to share existing records in case patients visit the other, share data between staff. They should use a connection speed of no less than 100mbp to assure efficiency. They should also use the same platform they use to work with, or create their own clinic system. Since it's a small clinic, they should be able to communicate with a bigger clinic, a hospital, that could maintain difficult and/or unfamiliar cases with professionals.

**Missing Points:**
- security

**Technical Errors:**
- No mention of redundancy, failover, or high-availability design despite the 'minimal downtime' requirement in the scenario
- No mention of data protection, encryption, access control, or compliance (e.g., HIPAA) for patient records
- Response focuses predominantly on staff allocation and organizational structure rather than network design

**Strengths:**
- Explicitly addresses growth from 30 to 80 staff and plans for expansion space
- Identifies budget as a constraint
- Mentions inter-site communication and record sharing as a business need
- Identifies the need for referral capability to a larger hospital

## REQ_002 | requirements_analysis | 1/10 FAIL (graded)

**Question:** A university building has 6 labs and 12 classrooms. Each lab has 35 PCs. WiFi must cover classrooms. Some devices are IoT sensors. The network must support online exams without drops. IT staff is small.

**Answer:**

> A university that would require 6 labs, 35 PCs, 12 classrooms, WiFi coverage, IoT sensors, online exams must not drop, small IT staff. So we need to build a server that can communicate with all the devices and maintain availability of an online examination that should not drop. Each lab has 35 PCs, so maybe build a server for each lab specified for that lab's purpose that can connect all 35 PCs to it without losing connectivity, which means there should be a backup server incase the main one(s) fail. 12 classrooms that should present, so it must have projection devices, one each. Since it's 12 classroom, they need one server they can connect to where only staff, admins, ITs can sign into it.

**Missing Points:**
- traffic types
- wireless coverage
- management
- segmentation

**Technical Errors:**
- A server does not connect PCs to a network; switches and routers perform that role. The student conflates a server with a network access device. ("build a server for each lab specified for that lab's purpose that can connect all 35 PCs to it")
- Projection devices are not a network design element and do not address any networking requirement. ("it must have projection devices, one each")

**Strengths:**
- Acknowledged the need for redundancy/backup to support availability of online exams ("there should be a backup server incase the main one(s) fail")

## LOG_001 | logical_design | 1/10 FAIL (graded)

**Question:** A mid size company has 3 departments: HR, Finance, Engineering. Engineering has heavy internal traffic and needs lab isolation. Finance needs strict access control. Provide a logical design approach.

**Answer:**

> A company with 3 departments, so each department must have their own portal specified for their tasks. Engineering have heavy internal traffic and needs lab isolation, which means we need to control traffic and filter them, we need to address performance techniques. Finance needs strict access, which means only them who have to view these data, I'll assume to maintain integrity which is a security feature. HR seems to not face a trouble and since they need to oversea staff and workplace, they could be update user information.

**Missing Points:**
- hierarchical design
- addressing plan
- routing approach
- redundancy

**Design Flaws:**
- Confuses network segmentation with a web 'portal' concept: 'each department must have their own portal specified for their tasks'
- No concrete mechanism for isolation (no VLANs, subnets, ACLs, or firewall rules mentioned): 'we need to control traffic and filter them'
- Dismisses HR entirely with no design consideration: 'HR seems to not face a trouble'
- Vague security claim with no implementation detail: 'I'll assume to maintain integrity which is a security feature'

**Strengths:**
- Attempts to address each department's stated requirement individually
- Recognises Engineering needs traffic control and isolation as a distinct concern

## PROT_001 | protocol_selection | 0/10 FAIL (guard_rejected)

**Question:** Choose a routing protocol for a campus network with multiple buildings and future growth. Justify your choice briefly.

**Reason:** answer too short to grade (under 20 characters)

## SEC_001 | security_strategy | 0/10 FAIL (guard_rejected)

**Question:** A company allows remote work. They host internal apps and a public website. Propose security strategies for internal and perimeter security.

**Reason:** answer too short to grade (under 20 characters)

