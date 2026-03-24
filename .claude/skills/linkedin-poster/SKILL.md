# LinkedIn Poster Skill

Automatically post on LinkedIn about your business to generate sales and engagement.

## What this skill does

This skill helps you maintain LinkedIn presence by:
1. Generating business-relevant post content
2. Creating drafts for approval
3. Posting to LinkedIn automatically (after approval)
4. Tracking post performance
5. Scheduling posts for optimal times
6. Following Company Handbook guidelines

## Prerequisites

- Playwright browser automation library
- LinkedIn account credentials
- Persistent browser session
- Business context in Company_Handbook.md

## Setup

1. Install Playwright: `pip install playwright`
2. Install browsers: `playwright install chromium`
3. First run will open LinkedIn for login
4. Session saved to `linkedin_session/` directory
5. Configure posting rules in Company_Handbook.md

## When to use

Run this skill:
- To create draft posts for approval
- After approving a draft in /Approved folder
- On a schedule (e.g., 3x per week)
- When you have business updates to share

## Usage

```bash
# Generate and create draft post
/linkedin-poster --draft-only true

# Post specific content (after approval)
/linkedin-poster --content "Excited to announce our new service..."

# Schedule a post
/linkedin-poster --schedule "2026-02-28T10:00:00Z"
```

## Workflow

### Draft Creation (Default)

1. **Read Business Context:**
   - Load Company_Handbook.md
   - Load Business_Goals.md
   - Review recent completed tasks in /Done

2. **Generate Post Content:**
   - Analyze recent achievements
   - Identify shareable wins
   - Create engaging post text
   - Add relevant hashtags
   - Include call-to-action

3. **Create Approval Request:**
   - Save draft to /Pending_Approval
   - Include preview and context
   - Wait for human approval

### Posting (After Approval)

1. **Load Approved Content:**
   - Read from /Approved folder
   - Verify content meets guidelines

2. **Authenticate LinkedIn:**
   - Load persistent session
   - Navigate to LinkedIn
   - Verify logged in

3. **Create Post:**
   - Click "Start a post"
   - Enter post content
   - Add hashtags
   - Preview post

4. **Publish:**
   - Click "Post" button
   - Verify post published
   - Capture post URL

5. **Log Activity:**
   - Move to /Done
   - Update Dashboard
   - Log to /Logs

## Post Content Guidelines

**Good Post Topics:**
- Recent project completions
- Client success stories (with permission)
- Industry insights and tips
- Behind-the-scenes of your work
- Milestones and achievements
- Helpful resources for your audience

**Avoid:**
- Overly promotional content
- Controversial topics
- Personal complaints
- Unverified claims
- Competitor bashing

## Post Format Template

```
[Hook - attention grabbing first line]

[Main content - 2-3 paragraphs]
- Share value or insight
- Tell a story
- Provide actionable tips

[Call to action]
- What should readers do?
- Comment, share, connect, visit website

#Hashtag1 #Hashtag2 #Hashtag3
```

## Approval Request Format

```markdown
---
type: linkedin_post
created: 2026-02-27T10:00:00Z
priority: medium
status: pending_approval
scheduled_for: 2026-02-28T10:00:00Z
---

## LinkedIn Post Draft

### Post Content
[Generated post text with hashtags]

### Context
- Based on: Recent project completion
- Target audience: Potential clients
- Goal: Generate leads
- Estimated reach: 500-1000 impressions

### Preview
[How it will look on LinkedIn]

### To Approve
Move this file to /Approved folder

### To Reject
Move this file to /Rejected folder with feedback
```

## Posting Schedule Recommendations

**Best Times to Post:**
- Tuesday-Thursday: 9-11 AM
- Wednesday: 12 PM (lunch break)
- Thursday: 5-6 PM (end of workday)

**Frequency:**
- 2-3 posts per week
- Consistent schedule
- Mix of content types

## Configuration

Edit `Company_Handbook.md` to customize:
- Posting frequency
- Content themes
- Hashtag strategy
- Target audience
- Approval requirements

## Security & Privacy

- LinkedIn credentials stored securely
- Session managed locally
- No third-party posting services
- All drafts require approval
- Compliance with LinkedIn terms

## Tracking & Analytics

After posting, the skill logs:
- Post URL
- Timestamp
- Content summary
- Engagement metrics (manual update)

## Troubleshooting

**Session expired:**
- Delete `linkedin_session/` folder
- Run skill to re-authenticate
- Log in with credentials

**Post failed:**
- Check LinkedIn connection
- Verify account not restricted
- Review post content for violations

**No content generated:**
- Update Business_Goals.md
- Add recent achievements to /Done
- Provide more business context
