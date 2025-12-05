# TripCompass UI Design Ideation

## Core User Flow

### 1. **Onboarding / Profile Setup**
**Purpose:** Collect user preferences before generating itinerary

**Components:**
- Welcome screen with TripCompass branding
- Step-by-step wizard or single-page form
- Progress indicator (Step 1 of 4, etc.)

**Input Fields:**
- **Trip Details:**
  - Destination (pre-filled: San Francisco, or dropdown)
  - Trip duration (slider: 1-7 days)
  - Total budget (input with currency selector)
  - Travel dates (calendar picker)
  
- **Travel Style:**
  - Pace selector: Slow / Moderate / Fast (with icons + descriptions)
    - Slow: "Take your time, enjoy longer visits"
    - Moderate: "Balanced pace, mix of activities"
    - Fast: "Pack in as much as possible"
  
- **Interests (Multi-select with sliders):**
  - Food & Dining (0-1.0 slider)
  - Museums & Culture (0-1.0 slider)
  - Outdoors & Parks (0-1.0 slider)
  - Shopping (0-1.0 slider)
  - Nightlife (0-1.0 slider)
  - Arts & Culture (0-1.0 slider)
  - Visual: Tag cloud or card-based selection
  
- **Must-Do / Can't-Do:**
  - "Must visit" searchable POI selector
  - "Avoid" searchable POI selector
  - Recent searches / Popular choices
  
- **Home Base:**
  - Hotel/neighborhood selector
  - Or: "I'll provide coordinates" (advanced)
  - Map preview showing location

**Visual Design:**
- Clean, modern form with card-based sections
- Icons for each interest category
- Real-time budget calculator (daily budget = total / days)
- Preview of what's being built

---

### 2. **Itinerary Generation / Loading**
**Purpose:** Show progress while AI generates itinerary

**Components:**
- Animated loading screen
- Progress steps:
  - "Analyzing your preferences..."
  - "Scoring 2,246+ activities..."
  - "Optimizing your route..."
  - "Finalizing your itinerary..."
- Estimated time: "~3-5 seconds"
- Fun facts about SF while loading

**Visual Design:**
- Smooth animations
- Progress bar or spinner
- Brand colors

---

### 3. **Main Itinerary View**
**Purpose:** Display the generated itinerary

**Layout Options:**

#### **Option A: Timeline View (Recommended)**
- Vertical timeline on left
- Day tabs at top (Day 1, Day 2, etc.)
- Each activity as a card with:
  - Time slot (09:30 - 11:00)
  - Activity name + category icon
  - Location (with mini map pin)
  - Cost badge
  - Predicted satisfaction (star rating or score)
  - Travel leg indicator (walk 12 min →)
  - Expandable details (description, tips, photos)

**Visual Elements:**
- Color-coded by category (museums = blue, parks = green, etc.)
- Transport mode icons (🚶 walk, 🚌 transit, 🚗 Uber)
- Satisfaction meter (visual bar or stars)
- Cost indicator (green = within budget, yellow = approaching limit)

#### **Option B: Map View**
- Interactive map (Google Maps or Mapbox)
- POIs plotted with category markers
- Route lines connecting activities
- Click marker → see activity details
- Toggle: Show/hide categories
- Day filter: Show only Day 1, Day 2, etc.

#### **Option C: List View**
- Compact list format
- Sortable columns: Time, Name, Cost, Satisfaction
- Quick filters: Category, Cost range, Time of day
- Expandable rows for details

**Recommended: Hybrid Approach**
- **Primary:** Timeline view (most intuitive)
- **Secondary tabs:** Map view, List view
- **Toggle between views** easily

---

### 4. **Activity Details Panel**
**Purpose:** Show detailed info when user clicks an activity

**Components:**
- Activity name (large, prominent)
- Category badge
- Time slot (start - end)
- Location (address + map preview)
- Cost breakdown
- Predicted satisfaction score + explanation
  - "High match because: You love museums (0.95) and this is highly rated (4.8)"
- Travel info:
  - From previous: "12 min walk from Contemporary Jewish Museum"
  - To next: "8 min walk to SFMOMA"
- Opening hours
- Tips / Notes (if available)
- "Remove from itinerary" button
- "Swap with similar" button

**Visual Design:**
- Slide-in panel from right (desktop)
- Full-screen modal (mobile)
- Smooth animations

---

### 5. **Day Summary Card**
**Purpose:** Quick overview of each day

**Components:**
- Day number + date
- Total activities count
- Total cost vs daily budget (progress bar)
- Total satisfaction score
- Activity time, transit time, buffer time
- Category breakdown (pie chart or bar)
- Feasibility indicator (✓ or ⚠️)

**Visual Design:**
- Card at top of each day section
- Color-coded budget bar (green/yellow/red)
- Compact, scannable

---

### 6. **Trip Overview Dashboard**
**Purpose:** High-level summary of entire trip

**Components:**
- Total trip stats:
  - Total cost vs total budget
  - Average satisfaction per day
  - Total activities
  - Feasibility status
- IQS Score display (large, prominent)
- Category distribution (all days combined)
- Budget breakdown (pie chart)
- Travel efficiency metric
- "Export itinerary" button
- "Regenerate" button (with options: more/less activities, different pace, etc.)

**Visual Design:**
- Dashboard-style layout
- Charts and graphs (using Chart.js or similar)
- Clean, professional

---

### 7. **Interactive Features**

#### **Drag & Drop Reordering**
- Allow users to drag activities to reorder
- Auto-recalculate times and travel
- Show conflicts if reordering breaks constraints

#### **Add/Remove Activities**
- "Add activity" button → search POIs
- Filter by category, cost, time
- Preview impact on itinerary (cost, time, satisfaction)
- "Remove" button on each activity
- Auto-optimize remaining schedule

#### **Swap Activities**
- "Swap with similar" → show alternatives
- Filtered by: same category, similar cost, nearby location
- Preview: "This swap will increase satisfaction by +0.3"

#### **Adjust Preferences**
- "Tweak preferences" button
- Quick adjust: More museums? Less cost? Faster pace?
- Regenerate with new preferences

#### **Time Adjustments**
- Click time → adjust start/end
- Auto-update subsequent activities
- Warn if conflicts arise

---

### 8. **Visual Design Elements**

#### **Color Scheme**
- Primary: Blue (trust, travel)
- Secondary: Green (parks, nature)
- Accent: Orange (energy, activities)
- Background: Light gray or white
- Cards: White with subtle shadows

#### **Typography**
- Headers: Bold, modern sans-serif (Inter, Poppins)
- Body: Clean, readable (Roboto, Open Sans)
- Monospace: For times (09:30)

#### **Icons**
- Category icons (museum, park, restaurant, etc.)
- Transport icons (walk, transit, car)
- Status icons (feasible, warning, error)
- Action icons (edit, delete, add, swap)

#### **Animations**
- Smooth transitions between views
- Loading states
- Hover effects on cards
- Success animations (checkmarks, confetti)

---

### 9. **Mobile Responsiveness**

#### **Mobile Layout**
- Stack timeline vertically
- Swipe between days
- Bottom sheet for activity details
- Simplified navigation (hamburger menu)
- Touch-friendly buttons (larger tap targets)

#### **Tablet Layout**
- Side-by-side: Timeline + Map
- Or: Timeline + Details panel

---

### 10. **Additional Features**

#### **Export Options**
- PDF export (printable itinerary)
- Calendar export (.ics file)
- Share link (generate shareable URL)
- Email itinerary

#### **Save & Load**
- Save itinerary to account
- Load previous itineraries
- "Fork" itinerary (create variant)

#### **Comparison Mode**
- "Compare with baseline" toggle
- Side-by-side: Baseline vs Neural Network
- Show improvement metrics

#### **Real-time Validation**
- Live feasibility checks
- Budget warnings
- Time conflict alerts
- Opening hours validation

#### **Social Features** (Optional)
- Share itinerary on social media
- "Save for later" (bookmark)
- Rate itinerary after trip

---

## Technology Stack Suggestions

### **Frontend Framework Options:**
1. **React + TypeScript** (Recommended)
   - Component-based, reusable
   - Great ecosystem (React Router, React Query)
   - Strong typing

2. **Next.js** (If you want SSR/SSG)
   - Server-side rendering
   - API routes built-in
   - Great for production

3. **Vue.js** (Alternative)
   - Simpler learning curve
   - Good for rapid prototyping

### **UI Component Libraries:**
- **Material-UI (MUI)** - Comprehensive, well-documented
- **Chakra UI** - Modern, accessible
- **Tailwind CSS** - Utility-first, highly customizable
- **Ant Design** - Enterprise-grade components

### **Maps:**
- **Google Maps API** - Most features, costs money
- **Mapbox** - Beautiful, customizable, free tier
- **Leaflet** - Open source, lightweight

### **Charts:**
- **Chart.js** - Simple, popular
- **Recharts** - React-specific
- **D3.js** - Most powerful, steep learning curve

### **State Management:**
- **React Context** - For simple state
- **Redux Toolkit** - For complex state
- **Zustand** - Lightweight alternative

### **Backend Integration:**
- **FastAPI** (Python) - Easy to integrate with your existing code
- **Flask** - Simpler, lighter
- **Express.js** (Node) - If you want full JS stack

---

## User Experience Flow

1. **Landing Page**
   - Hero section: "Plan Your Perfect Trip"
   - Demo video/GIF
   - "Get Started" CTA

2. **Profile Setup** (2-3 minutes)
   - Guided wizard
   - Progress indicator
   - Save progress option

3. **Generation** (3-5 seconds)
   - Loading animation
   - Build anticipation

4. **Itinerary Review** (Main interaction)
   - Explore timeline
   - Click activities for details
   - Make adjustments
   - View on map

5. **Finalization**
   - Review summary
   - Export options
   - Share or save

---

## Key Design Principles

1. **Clarity First** - Easy to understand at a glance
2. **Progressive Disclosure** - Show details when needed
3. **Feedback** - Always show what's happening
4. **Flexibility** - Allow customization
5. **Delight** - Small animations, pleasant colors
6. **Accessibility** - WCAG compliant, keyboard navigation

---

## MVP vs Full Feature Set

### **MVP (Minimum Viable Product):**
- Profile setup form
- Itinerary generation
- Timeline view
- Basic activity details
- Day summary
- Export to PDF

### **Full Feature Set:**
- All MVP features +
- Map view
- Drag & drop reordering
- Add/remove activities
- Swap suggestions
- Multiple transport modes
- Save/load itineraries
- Comparison mode
- Mobile app

---

## Next Steps

1. **Choose tech stack** (React + TypeScript recommended)
2. **Create wireframes** (Figma, Sketch, or paper)
3. **Build MVP** (focus on core flow first)
4. **Iterate** (add features based on user feedback)

Would you like me to:
- Create a basic React component structure?
- Design specific wireframes?
- Build a simple HTML/CSS prototype?
- Set up the project structure?

