"""Benchmark authoring only. Never imported by the predictor or API adapter."""
from collections import Counter
from datetime import datetime,timezone
from .common import BASE,ROOT,LOCAL,SOURCE_SHA,read,write,sha,verify_legacy

def main():
    verify_legacy()
    if (BASE/'benchmarks/freeze.json').exists():raise ValueError('Already frozen')
    old=read(ROOT/'advanced/benchmarks/test.gold.json');dev=[]
    for i,q in enumerate(old,1):
        dev.append({**q,'id':f'ADV2-DEV-{i:02d}','previous_id':q['id'],
                    'provenance':'Previously evaluated v1 test, now development data only; never claimed as fresh holdout.'})
    test=[]
    def ev(p,b,loc,fact):return {'page':p,'printed_page':p-10,'bbox':b,'locator':loc,'fact':fact,
        'source_check':'Original NASA PDF render read directly, with native text used only as supporting access'}
    def add(group,q,a,note,*e,units='none'):
        test.append({'id':f'ADV2-TEST-{len(test)+1:02d}','question':q,'primary_group':group,
            'answerable':group!='unanswerable','expected':a,'units_calculation':units,
            'evidence':list(e),'independence_note':note})
    add('table','In Table 4.1-1, list all example stakeholders for Phase F.',
        'Customer; NASA Headquarters; operators; safety; planetary protection; public.',
        'New table and stakeholder row; old Phase F question asked purpose, not stakeholder membership.',
        ev(57,[.09,.34,.91,.38],'Table 4.1-1, Phase F row','All six stakeholder entries required'))
    add('table','In Table 5.3-1, what procedure copy must a Verification Report include, and what does its final entry require about test results and acceptability?',
        'Copy of the as-run procedure (may include redlines); authentication of test results and authorization of acceptability.',
        'New Verification Report cells, not old verification method/validation-method questions.',
        ev(104,[.50,.50,.91,.63],'Table 5.3-1, Verification Report column, last two entries','As-run copy plus authentication/authorization'))
    add('table','In Table 6.1-1, which two Instrument Subteam subsystem entries appear after Mechanism Drive Electronics and before Control Subsystem?',
        'Detector Subsystem and Optics Subsystem.',
        'New team-discipline table and ordered row lookup.',
        ev(128,[.09,.61,.91,.69],'Table 6.1-1, Instrument Subteam, rows between Mechanism Drive Electronics and Control','Detector then Optics'))
    add('table','In Table 6.1-2, which middle-column facility shares the row with Robotics Labs in the left column?',
        'Vacuum Chambers.',
        'New facility table and spatial row/column alignment.',
        ev(130,[.09,.26,.91,.29],'Table 6.1-2, Robotics Labs row, middle column','Vacuum Chambers'))
    add('table','In Table 6.6-1, for Technical data capture, to whom are integrity-check anomalies reported and for what purpose? Also name the inventory output.',
        'Report anomalies/variances to the authors or generators of the data for correction; Stored data inventory.',
        'New technical-data task table; does not repeat old metadata Rationale item.',
        ev(166,[.09,.14,.91,.44],'Table 6.6-1, Technical data capture, Tasks and Expected Outcomes','Authors/generators, correction, stored data inventory'))
    add('table','At KDP B in Table G.1-1, which two products are updated and in which plan are they incorporated?',
        'Technology Development Plan and Technology Readiness Assessment (TRA), incorporated in the preliminary project plan.',
        'New technology-assessment gate table; different from old life-cycle review baselines.',
        ev(217,[.09,.24,.91,.29],'Table G.1-1, KDP B row','Both updated products and preliminary project plan'))
    add('diagram','In Figure 5.0-1, which two processes are grouped under Design Realization and which two under Evaluation Processes?',
        'Design Realization: Product Implementation and Product Integration. Evaluation: Product Verification and Product Validation.',
        'New grouping relationships in a different informative diagram.',
        ev(88,[.14,.11,.71,.29],'Figure 5.0-1, Design Realization and Evaluation columns','Four processes in their correct groups'))
    add('diagram','In Figure 5.2-1, what central activity follows Confirm that received products have been validated and precedes Assemble and integrate the received products?',
        'Prepare the integration environment for assembly and integration.',
        'New integration-process edge; old dev predecessor question used a different requirements process.',
        ev(96,[.36,.22,.63,.39],'Figure 5.2-1, middle three yellow blocks','Preparation of integration environment between named nodes'))
    add('diagram','In Figure 5.5-1, to which two destinations can Delivered End Product With Applicable Documentation go, and which route is marked recursive?',
        'To the end user or to Product Integration Process; the Product Integration route is the recursive loop.',
        'New transition output and recursive-loop relationship, not the old Lowest Level diamond.',
        ev(117,[.65,.12,.82,.23],'Figure 5.5-1, top-right output and recipient note','End user or Product Integration Process (recursive loop)'))
    add('diagram','In Figure 6.3-1, which outputs go to Configuration Management and which output goes to Technical Data Management?',
        'Interface Control Documents and Approved Interface Requirement Changes go to Configuration Management. Interface Management Work Products go to Technical Data Management.',
        'New interface-management output destinations, not old expectations-definition recipients.',
        ev(146,[.65,.13,.84,.38],'Figure 6.3-1, three right-hand outputs and recipient labels','Two CM outputs, one TDM output'))
    add('diagram','In Figure 6.5-4, identify both branches immediately after CCB step 7: their step labels, responsible lanes, and activities.',
        '8a in Actionees: Complete assigned actions. 8b in CM Function: Release CCB minutes and Track actions.',
        'New change-control branching diagram, not old five-element CM figure or risk Yes branch.',
        ev(158,[.23,.43,.91,.75],'Figure 6.5-4, outgoing step 7 arrows to 8a and 8b; lane headings above','8a Actionees; 8b CM Function'))
    add('chart','In Figure 2.5-1, what three intermediate percentages are explicitly labelled along the Committed Life Cycle Costs curve before it reaches 100%?',
        '45%, 75%, 90%.',
        'Old questions targeted expended-cost blocks and endpoint multipliers; committed-curve labels were not asked.',
        ev(23,[.22,.09,.71,.25],'Figure 2.5-1, upper committed-cost curve, three intermediate percentage labels','45,75,90 percent'),units='percent; no calculation')
    add('chart','In Figure 2.5-1, what multiplier range is labelled in the middle of the Cost to Change Design Direction arrow, between its early and late labels?',
        '20–100x.',
        'Old dev asked only the two endpoints 3–6x and 500–1000x, not the middle value.',
        ev(23,[.42,.18,.53,.24],'Figure 2.5-1, middle teal-arrow multiplier label','20–100x'),units='dimensionless multiplier')
    add('chart','In Figure 2.5-1, what does the horizontal axis represent and how is the vertical axis labelled?',
        'Horizontal: Time. Vertical: Cumulative Percentage Life Cycle Cost against Time.',
        'Old axes question concerned Figure 4.4-3, with different quantities and units.',
        ev(23,[.14,.08,.82,.45],'Figure 2.5-1, axis labels','Time; cumulative percentage life-cycle cost against time'),units='time axis not numerically scaled; vertical percentage')
    add('chart','In Figure 4.4-3, what do the differently shaded areas represent?',
        'Different levels of uncertainty.',
        'Old chart test asked dashed lines/direction and axes; shading meaning is a new visual encoding.',
        ev(81,[.09,.09,.49,.50],'Figure 4.4-3, shaded ellipses and Note','Shaded areas indicate different uncertainty levels'))
    add('chart','Using Figure 4.4-3 and its explanation, contrast concept B with concept C in terms of risk of an expensive failure and the cost/effectiveness location shown for C.',
        'B has little risk in effectiveness or cost. C has high risk of expensive failure, shown by probability near the x axis at high cost and essentially no effectiveness.',
        'New risk-pattern comparison; old questions never asked the A/B/C concepts.',
        ev(81,[.09,.09,.49,.90],'Figure 4.4-3, B and C annotations, probability cloud and lower-left explanatory paragraph','B low risk; C expensive failure, high cost near zero effectiveness'))
    add('multi_hop','Combine Table 4.2-2 and Appendix C.2: which metadata item records who writes/manages/approves requirement changes, and what grammatical voice should a personnel requirement use?',
        'Owner is the person/group responsible for writing, managing and/or approving changes. Use active voice, identifying the responsible party who shall perform the action.',
        'Unused Owner row plus unused active-voice checklist; old questions asked Rationale, verification level, modals and WHAT/HOW.',
        ev(69,[.09,.69,.91,.74],'Table 4.2-2, Owner row','Responsible person/group for writing/managing/approving changes'),
        ev(207,[.09,.44,.49,.58],'C.2 Editorial Checklist, Personnel Requirement','Active voice; responsible party shall perform'))
    add('multi_hop','Combine Table 2.2-1 and Figure G.4-1: give the full name of Phase A and the formulation criterion at TRL 2.',
        'Phase A: Concept and Technology Development. TRL 2: Technology concept and/or application formulated.',
        'Different phase and TRL from earlier B/TRL6 and E/TRL9 pairs.',
        ev(19,[.09,.24,.91,.34],'Table 2.2-1, Phase A name','Concept and Technology Development'),
        ev(221,[.27,.50,.68,.57],'Figure G.4-1, TRL 2 label','Technology concept/application formulated'))
    add('multi_hop','Using Section 3.4 and Table 2.1-1, in which phase is the SEMP baselined, and list all AS9100 requirements mapped to Technical Planning.',
        'SEMP is baselined in Phase A. Technical Planning maps to Planning of Product Realization; Review of Requirements; Measurement, Analysis and Improvement.',
        'Unused SEMP timing fact and unused Technical Planning mapping, not old Phase B commitment or Decision Analysis row.',
        ev(35,[.09,.32,.49,.56],'Section 3.4 continuation, SEMP paragraph','SEMP baselined in Phase A'),
        ev(17,[.09,.68,.91,.73],'Table 2.1-1, Technical Planning row','All three AS9100 mappings'))
    add('multi_hop','Combine Table 2.1-1 with Figure 6.8-2: what AS9100 requirement maps to Technical Risk Management, and where does the No branch of Net beneficial to reduce uncertainty? lead before deliberation?',
        'AS9100 Risk Management. The No branch leads to Risk & Performance Measurement Results, which then feed Deliberation and Recommending a Decision Alternative.',
        'Unused Technical Risk mapping plus the other risk diamond/No branch; old test asked robust Yes branch only.',
        ev(17,[.09,.76,.91,.80],'Table 2.1-1, Technical Risk Management row','Risk Management'),
        ev(176,[.65,.15,.91,.40],'Figure 6.8-2, lower uncertainty diamond, No arrow and results box','No -> Risk & Performance Measurement Results -> Deliberation'))
    add('text','In the Section 4.1 discussion of Needs, Goals, and Objectives, how many needs should a need statement express, and should it identify the problem or the solution?',
        'A single need; the statement should relate to the problem to be solved, not the solution.',
        'Unused Need definition, different from old Goals measurability question.',
        ev(59,[.09,.74,.49,.91],'Need definition bullet, lower-left column','Single/singular need; problem not solution'))
    add('text','According to Appendix C.3, should a requirement be stated positively or negatively, and what example of negative phrasing is given?',
        'Positively; the negative example is shall not.',
        'Unused positive-statement checklist item; old C.1 modalities and WHAT/HOW target different criteria.',
        ev(207,[.51,.78,.91,.85],'C.3 General Goodness Checklist, positive statement checkbox','Positively, as opposed to shall not'))
    add('text','In Types of Configuration Management Changes, who must coordinate and approve a change affecting an external interface?',
        'All stakeholders affected must coordinate and approve it.',
        'New conditional interface-change rule, not old CM elements or software pricing.',
        ev(159,[.09,.17,.91,.24],'Types of Configuration Management Changes, Engineering Change paragraph','All stakeholders affected'))
    add('text','According to Section 2.4, which document does validation relate back to, and is validation limited to delivery of end products?',
        'The ConOps document. No: validation can be performed in each development phase using phase products such as models, not only at delivery using end products.',
        'New validation reference-document/timing facts, distinct from old most-resource-intensive Test method.',
        ev(21,[.09,.71,.49,.87],'Section 2.4, final left-column validation paragraph','ConOps; each development phase with phase products'))
    absent=[
      ('What universal minimum number of configuration audits per year does this handbook mandate for every NASA project?',['configuration audits','per year'],'6.5 Configuration Management'),
      ('What fixed maximum interface response latency in milliseconds is prescribed for every system in this handbook?',['latency','milliseconds','interface'],'6.3 Interface Management'),
      ('Which single vendor of requirements-management software does this handbook require every NASA project to buy?',['vendor','requirements management','software'],'6.2 Requirements Management'),
      ('What exact mass of returned samples in grams must every Phase F closeout analyze?',['samples','grams','Phase F'],'3.9 Phase F'),
      ('What universal fixed number of thermal-vacuum cycles is required for verification of every product?',['thermal','vacuum','cycles'],'5.3 Product Verification'),
      ('What mandatory maximum number of design alternatives may every trade study evaluate?',['alternatives','maximum','trade study'],'4.4 Design Solution Definition and 6.8 Decision Analysis')]
    pages=read(LOCAL/'index.json')
    for q,terms,section in absent:
        add('unanswerable',q,'Abstain without inventing a universal mandate/value/vendor.',
            'New missing fact/entity; not a rephrase of old absence questions.',
            {'absence_check':{'related_section':section,'terms':terms,
                'term_hits':{term:[p['page'] for p in pages if term.casefold() in p['text'].casefold()] for term in terms},
                'method':'Whole-corpus phrase scan and direct review of relevant source guidance; related examples/qualitative statements do not establish requested universal rule.'}})
    for split,rows in [('dev',dev),('test',test)]:
        write(BASE/f'benchmarks/{split}.gold.json',rows)
        write(BASE/f'benchmarks/{split}.inputs.json',[{'id':q['id'],'question':q['question']} for q in rows])
    previous=read(ROOT/'advanced/benchmarks/dev.gold.json')+old
    assert not {q['question'] for q in previous}&{q['question'] for q in test}
    write(BASE/'benchmarks/independence_review.json',{'previous_question_ids':[q['id'] for q in previous],
        'method':'Manual target-fact comparison against ALL prior dev and test questions; exact question intersection also checked.',
        'cases':[{'id':q['id'],'reason':q['independence_note']} for q in test],
        'limitations':'Same NASA document and two quantitative charts; source-page overlap permitted, answer targets differ. Not a new document generalization test.'})
    files=sorted((BASE/'benchmarks').glob('*.json'))
    write(BASE/'benchmarks/freeze.json',{'frozen_at':datetime.now(timezone.utc).isoformat(),
        'stage':'Before ANY v2 retrieval/model experiments','source_sha256':SOURCE_SHA,
        'groups':{s:dict(Counter(q['primary_group'] for q in r)) for s,r in [('dev',dev),('test',test)]},
        'files_sha256':{str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in files},
        'legacy_snapshot_sha256':sha(BASE/'legacy_snapshot.json')})
    print('Frozen v2: dev 30 inherited for development; fresh independent test 30.')

if __name__=='__main__':main()
