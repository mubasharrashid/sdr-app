# n8n Workflow Updates for BANT Qualification

This document provides the updated code snippets for the "8) Email Auto Replies Agent" n8n workflow to support BANT (Budget, Authority, Need, Timeline) qualification.

## Overview of Changes

1. **Extract Relevant Data** node - Updated to parse BANT qualification data from AI response
2. **Insert Chat History** node - Updated to save BANT tracking data
3. **Determine Sales Person Assignment** node - Updated to include BANT notes
4. **Insert Meeting Record** node - Updated to include BANT prep notes

---

## 1. Updated "Extract Relevant Data" Code Node

Replace the existing code in the "Extract Relevant Data" node with:

```javascript
// Find the agent message dynamically
const agentMessage = ($json.messages || []).find(
  m => m.role === "agent" && m.content
);

if (!agentMessage) {
  throw new Error("No agent message found in Retell response");
}

// Parse the JSON content safely
let aiData;
try {
  aiData = JSON.parse(agentMessage.content);
} catch (err) {
  throw new Error("Failed to parse agent content JSON");
}

// Build base output
const output = {
  intent: aiData.intent,
  confidence: aiData.confidence,
  reply_draft: aiData.reply_draft,
  ask_for_availability: aiData.ask_for_availability,
  reason: aiData.reason,
  message_from_agent_time: new Date(agentMessage.created_timestamp)
};

// Add availability data if present (for AVAILABILITY_PROVIDED intent)
if (aiData.availability) {
  output.availability_date = aiData.availability.date;
  output.availability_time = aiData.availability.time;
  output.availability_timezone = aiData.availability.timezone;
  
  // Create ISO datetime for calendar event
  output.meeting_start_datetime = `${aiData.availability.date}T${aiData.availability.time}:00`;
  
  // Calculate end time (30 minutes later)
  const startTime = new Date(`${aiData.availability.date}T${aiData.availability.time}:00`);
  const endTime = new Date(startTime.getTime() + 30 * 60000); // Add 30 minutes
  const endTimeString = endTime.toISOString().split('T')[1].substring(0, 5); // Extract HH:MM
  output.meeting_end_datetime = `${aiData.availability.date}T${endTimeString}:00`;
}

// ========================================
// BANT QUALIFICATION DATA EXTRACTION
// ========================================
if (aiData.bant_qualification) {
  const bant = aiData.bant_qualification;
  
  // Individual BANT scores
  output.bant_budget_score = bant.budget?.score || 0;
  output.bant_authority_score = bant.authority?.score || 0;
  output.bant_need_score = bant.need?.score || 0;
  output.bant_timeline_score = bant.timeline?.score || 0;
  
  // Individual BANT details
  output.bant_budget_details = bant.budget?.details || null;
  output.bant_authority_details = bant.authority?.details || null;
  output.bant_need_details = bant.need?.details || null;
  output.bant_timeline_details = bant.timeline?.details || null;
  
  // Individual BANT identified flags
  output.bant_budget_identified = bant.budget?.identified || false;
  output.bant_authority_identified = bant.authority?.identified || false;
  output.bant_need_identified = bant.need?.identified || false;
  output.bant_timeline_identified = bant.timeline?.identified || false;
  
  // Overall BANT data
  output.bant_overall_score = bant.overall_score || 0;
  output.bant_qualification_status = bant.qualification_status || 'unqualified';
  output.bant_sales_notes = bant.sales_notes || null;
  
  // Full BANT data for storage
  output.bant_data = bant;
}

// Return structured output for next nodes
return [
  {
    json: output
  }
];
```

---

## 2. Updated "Insert Chat History" Supabase Node

Update the fields in the "Insert Chat History" node to include BANT data:

| Field Name | Value |
|------------|-------|
| chat_id | `{{ $('Fetch Chat ID and Email Reply ID').item.json.chat_id }}` |
| email_reply_id | `{{ $('Fetch Chat ID and Email Reply ID').item.json.id }}` |
| message_from_email | `{{ $('Webhook').item.json.body.body }}` |
| message_from_agent_ai | `{{ $json.reply_draft }}` |
| ask_for_availability | `{{ $json.ask_for_availability }}` |
| confidence_score | `{{ $json.confidence }}` |
| intent_diagnosed_by_ai | `{{ $json.intent }}` |
| message_from_agent_time | `{{ $json.message_from_agent_time }}` |
| tenant_id | `176f02d9-9e7b-45f0-bac1-918f5d8fbd26` |
| **bant_budget_identified** | `{{ $json.bant_budget_identified || false }}` |
| **bant_authority_identified** | `{{ $json.bant_authority_identified || false }}` |
| **bant_need_identified** | `{{ $json.bant_need_identified || false }}` |
| **bant_timeline_identified** | `{{ $json.bant_timeline_identified || false }}` |
| **bant_data** | `{{ JSON.stringify($json.bant_data || {}) }}` |

---

## 3. Add "Update Lead BANT" Supabase Node

Add a new Supabase node after "Insert Chat History" to update the lead's BANT qualification data:

**Node Name:** Update Lead BANT Scores

**Operation:** Update

**Table:** leads

**Filters:**
- Key: `id`
- Condition: `eq`
- Value: `{{ $('Fetch Chat ID and Email Reply ID').item.json.lead_id }}`

**Fields to Update:**

| Field Name | Value |
|------------|-------|
| bant_budget_score | `{{ Math.max($('Fetch Lead Details').item.json.bant_budget_score || 0, $('Extract Relevant Data').item.json.bant_budget_score || 0) }}` |
| bant_authority_score | `{{ Math.max($('Fetch Lead Details').item.json.bant_authority_score || 0, $('Extract Relevant Data').item.json.bant_authority_score || 0) }}` |
| bant_need_score | `{{ Math.max($('Fetch Lead Details').item.json.bant_need_score || 0, $('Extract Relevant Data').item.json.bant_need_score || 0) }}` |
| bant_timeline_score | `{{ Math.max($('Fetch Lead Details').item.json.bant_timeline_score || 0, $('Extract Relevant Data').item.json.bant_timeline_score || 0) }}` |
| bant_budget_details | `{{ $('Extract Relevant Data').item.json.bant_budget_details || $('Fetch Lead Details').item.json.bant_budget_details }}` |
| bant_authority_details | `{{ $('Extract Relevant Data').item.json.bant_authority_details || $('Fetch Lead Details').item.json.bant_authority_details }}` |
| bant_need_details | `{{ $('Extract Relevant Data').item.json.bant_need_details || $('Fetch Lead Details').item.json.bant_need_details }}` |
| bant_timeline_details | `{{ $('Extract Relevant Data').item.json.bant_timeline_details || $('Fetch Lead Details').item.json.bant_timeline_details }}` |
| bant_sales_notes | `{{ $('Extract Relevant Data').item.json.bant_sales_notes }}` |

**Note:** The `Math.max()` ensures we keep the highest score achieved across conversations (BANT scores should only increase, not decrease).

---

## 4. Updated "Determine Sales Person Assignment" Code Node

Update the code to include BANT notes in the output:

```javascript
// Get lead data
const lead = $('Fetch Lead Details').item.json;
const salesPersons = $('Fetch Sales Persons').all().map(item => item.json);
const bantData = $('Extract Relevant Data').item.json;

let assignedPerson = null;

// STEP 1: Check if lead has ICP reference person assigned
if (lead.icp_reference_person) {
  assignedPerson = salesPersons.find(sp => 
    sp.name && sp.name.toLowerCase() === lead.icp_reference_person.toLowerCase()
  );
  
  if (assignedPerson) {
    console.log(`✅ Assigned via ICP Reference: ${assignedPerson.name}`);
  }
}

// STEP 2: If no ICP reference, match by organization industry
if (!assignedPerson && lead.organization_industry) {
  const orgIndustry = lead.organization_industry.toLowerCase();
  
  assignedPerson = salesPersons.find(sp => {
    if (!sp.industry_type) return false;
    
    const industries = sp.industry_type.toLowerCase();
    
    if (industries.includes('oil') || industries.includes('energy') || industries.includes('renewable')) {
      return orgIndustry.includes('oil') || 
             orgIndustry.includes('energy') || 
             orgIndustry.includes('power') ||
             orgIndustry.includes('renewable') ||
             orgIndustry.includes('gas');
    }
    
    if (industries.includes('ship') || industries.includes('marine')) {
      return orgIndustry.includes('ship') || 
             orgIndustry.includes('marine') || 
             orgIndustry.includes('maritime') ||
             orgIndustry.includes('port');
    }
    
    if (industries.includes('perfume') || industries.includes('dg')) {
      return orgIndustry.includes('perfume') || 
             orgIndustry.includes('fragrance') ||
             orgIndustry.includes('chemical') ||
             orgIndustry.includes('cosmetic');
    }
    
    if (industries.includes('overseas') || industries.includes('agent')) {
      return orgIndustry.includes('logistics') || 
             orgIndustry.includes('freight') ||
             orgIndustry.includes('forwarding');
    }
    
    return false;
  });
  
  if (assignedPerson) {
    console.log(`✅ Assigned via Industry Match: ${assignedPerson.name}`);
  }
}

// STEP 3: Default fallback
if (!assignedPerson) {
  assignedPerson = salesPersons.find(sp => 
    sp.industry_type && sp.industry_type.toLowerCase().includes('general enquiries')
  ) || salesPersons.find(sp => sp.name === 'Manas');
  
  console.log(`⚠️ No match found. Assigned to default: ${assignedPerson?.name || 'None'}`);
}

// STEP 4: Build output data
if (!assignedPerson) {
  throw new Error('❌ No sales person could be assigned. Check sales_person table.');
}

// ========================================
// BUILD BANT SUMMARY FOR SALES PERSON
// ========================================
let bantSummary = '';

if (bantData.bant_sales_notes) {
  bantSummary = bantData.bant_sales_notes;
} else {
  // Build summary from individual BANT components
  const bantItems = [];
  
  if (bantData.bant_budget_identified && bantData.bant_budget_details) {
    bantItems.push(`💰 BUDGET: ${bantData.bant_budget_details}`);
  }
  if (bantData.bant_authority_identified && bantData.bant_authority_details) {
    bantItems.push(`👤 AUTHORITY: ${bantData.bant_authority_details}`);
  }
  if (bantData.bant_need_identified && bantData.bant_need_details) {
    bantItems.push(`🎯 NEED: ${bantData.bant_need_details}`);
  }
  if (bantData.bant_timeline_identified && bantData.bant_timeline_details) {
    bantItems.push(`⏰ TIMELINE: ${bantData.bant_timeline_details}`);
  }
  
  if (bantItems.length > 0) {
    bantSummary = bantItems.join('\n');
  } else {
    bantSummary = 'No BANT information collected yet. Gather qualification data during the meeting.';
  }
}

const qualificationStatus = bantData.bant_qualification_status || 'unqualified';
const overallScore = bantData.bant_overall_score || 0;

return {
  json: {
    // Sales person info
    sales_person_id: assignedPerson.id,
    sales_person_name: assignedPerson.name,
    sales_person_email: assignedPerson.email,
    sales_person_industry: assignedPerson.industry_type,
    
    // Assignment reason
    assignment_method: lead.icp_reference_person ? 'ICP_REFERENCE' : 
                       lead.organization_industry ? 'INDUSTRY_MATCH' : 'DEFAULT',
    
    // Lead info
    customer_email: lead.email,
    customer_name: lead.full_name || lead.first_name || 'there',
    customer_company: lead.organization_name,
    customer_industry: lead.organization_industry,
    
    // Email data
    email_subject: $('Webhook').item.json.body.subject,
    email_body: $('Webhook').item.json.body.body,
    email_thread_id: $('Webhook').item.json.body.thread_id,
    
    // AI data
    ai_reply: $('Extract Relevant Data').item.json.reply_draft,
    ai_intent: $('Extract Relevant Data').item.json.intent,
    ai_confidence: $('Extract Relevant Data').item.json.confidence,
    ask_for_availability: $('Extract Relevant Data').item.json.ask_for_availability || false,
    
    // BANT data for meeting prep
    bant_qualification_status: qualificationStatus,
    bant_overall_score: overallScore,
    bant_summary: bantSummary,
    bant_prep_notes: `
=== BANT QUALIFICATION SUMMARY ===
Status: ${qualificationStatus.toUpperCase()} (Score: ${overallScore}/12)

${bantSummary}

=================================
    `.trim()
  }
};
```

---

## 5. Updated "Insert Meeting Record" Supabase Node

Update the fields to include BANT prep notes:

| Field Name | Value |
|------------|-------|
| lead_id | `{{ $('Fetch Lead Details').item.json.id }}` |
| email | `{{ $('Determine Sales Person Assignment').item.json.customer_email }}` |
| medium | `email` |
| booking_date | `{{ $('Extract Relevant Data').item.json.availability_date }}` |
| booking_time | `{{ $('Extract Relevant Data').item.json.availability_time }}` |
| timezone | `{{ $('Extract Relevant Data').item.json.availability_timezone }}` |
| assigned_to | `{{ $('Determine Sales Person Assignment').item.json.sales_person_email }}` |
| tenant_id | `176f02d9-9e7b-45f0-bac1-918f5d8fbd26` |
| **ai_prep_summary** | `{{ $('Determine Sales Person Assignment').item.json.bant_prep_notes }}` |

---

## 6. Updated "Forward Thread to Procurement" HTTP Request Node

Update the email body to include BANT information:

```json
{
  "personalizations": [{"to": [{"email": "procurement@rrrshipping.net"}]}],
  "from": {"email": "info@rrrshipping.net", "name": "RRR Shipping - Auto Forward"},
  "reply_to": {"email": "{{ $('Webhook').item.json.body.from }}"},
  "subject": "[PRICING - QUOTATION REQUEST] {{ $('Webhook').item.json.body.subject }}",
  "content": [{
    "type": "text/html",
    "value": "<h3>🔔 New Pricing/Quotation Request</h3><hr><p><strong>From:</strong> {{ $('Webhook').item.json.body.from }}</p><p><strong>Date:</strong> {{ $('Webhook').item.json.body.date }}</p><p><strong>Original Subject:</strong> {{ $('Webhook').item.json.body.subject }}</p><hr><h4>Customer Message:</h4><blockquote style='background: #f5f5f5; padding: 15px; border-left: 4px solid #007bff;'>{{ $('Webhook').item.json.body.body }}</blockquote><hr><h4>AI Assessment:</h4><p><strong>Intent:</strong> {{ $('Extract Relevant Data').item.json.intent }}</p><p><strong>Confidence:</strong> {{ $('Extract Relevant Data').item.json.confidence }}</p><p><strong>Reason:</strong> {{ $('Extract Relevant Data').item.json.reason }}</p><hr><h4>🎯 BANT Qualification:</h4><p><strong>Status:</strong> {{ $('Extract Relevant Data').item.json.bant_qualification_status || 'unqualified' }}</p><p><strong>Score:</strong> {{ $('Extract Relevant Data').item.json.bant_overall_score || 0 }}/12</p><p><strong>Sales Notes:</strong> {{ $('Extract Relevant Data').item.json.bant_sales_notes || 'No BANT data collected yet' }}</p><hr><p><em>Please respond directly to this email to reply to the customer.</em></p>"
  }]
}
```

---

## Summary of Database Changes Required

Before deploying these workflow changes, run the migration:

```sql
-- Run migration 009_add_bant_qualification.sql
```

This adds the following columns:
- `leads` table: BANT scores, details, overall score, qualification status, sales notes
- `leads_ai_conversation` table: BANT tracking flags and data JSON

---

## Testing Checklist

1. [ ] Run the database migration
2. [ ] Update Retell AI agent with the new prompt (see `app/prompts/chat_agent.py`)
3. [ ] Update the "Extract Relevant Data" code node
4. [ ] Add the "Update Lead BANT" Supabase node
5. [ ] Update "Insert Chat History" fields
6. [ ] Update "Determine Sales Person Assignment" code
7. [ ] Update "Insert Meeting Record" fields
8. [ ] Update "Forward Thread to Procurement" email body
9. [ ] Test with sample emails to verify BANT extraction
10. [ ] Verify BANT notes appear in meeting records
