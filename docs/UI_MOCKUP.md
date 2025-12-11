# Archive Converter - UI Mockup Specification

**Version**: 1.0.0
**Date**: 2025-12-11
**Target**: WSOP Poker Video Archive Management System
**Framework**: React + Material-UI (MUI)

---

## 1. Design Principles

### 1.1 User-Centered Goals
- **Quick Access**: 영상 검색 및 필터링 2초 내 완료
- **Efficient Workflow**: Asset → Segment 편집이 단일 플로우로 연결
- **Visual Clarity**: 타임라인 기반 세그먼트 시각화로 직관적 탐색
- **Accessibility**: WCAG 2.1 AA 준수, 키보드 단축키 지원

### 1.2 Design System
```yaml
Typography:
  Heading: Roboto Bold (24px, 20px, 16px)
  Body: Roboto Regular (14px)
  Monospace: Fira Code (파일명, 시간코드)

Colors:
  Primary: #1976d2 (MUI Blue)
  Secondary: #dc004e (Poker Red)
  Background: #f5f5f5 (Light Gray)
  Surface: #ffffff
  Text Primary: rgba(0,0,0,0.87)
  Text Secondary: rgba(0,0,0,0.6)

Spacing:
  Grid: 8px base unit
  Container: 1280px max-width
  Card Padding: 16px
```

---

## 2. Information Architecture

```
┌─ Archive Converter ──────────────────────────────────┐
│                                                       │
├─ 1. Dashboard (Overview)                             │
│   ├─ Statistics Cards                                │
│   ├─ Recent Activity                                 │
│   └─ Quick Actions                                   │
│                                                       │
├─ 2. Assets (Video Library)                           │
│   ├─ Search & Filters                                │
│   ├─ Asset Grid/List View                            │
│   └─ Batch Operations                                │
│                                                       │
├─ 3. Asset Detail                                     │
│   ├─ Video Player                                    │
│   ├─ Metadata Panel                                  │
│   ├─ Segment Timeline                                │
│   └─ Segment List                                    │
│                                                       │
├─ 4. Segment Editor                                   │
│   ├─ Playback Controls                               │
│   ├─ Tagging Interface                               │
│   ├─ Player/Hand Rating                              │
│   └─ Export Options                                  │
│                                                       │
└─ 5. Settings                                         │
    ├─ Tag Management                                  │
    ├─ Export Presets                                  │
    └─ User Preferences                                │
```

---

## 3. Screen Wireframes

### 3.1 Main Dashboard (Overview)

```
┌──────────────────────────────────────────────────────────────────┐
│ ☰ Archive Converter                    [Search...] 🔔 👤        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ Statistics ─────────────────────────────────────────────┐   │
│  │                                                           │   │
│  │  📁 Total Assets        🎬 Segments         ⏱ Duration   │   │
│  │     1,247                  3,891               847h 23m   │   │
│  │                                                           │   │
│  │  🏷 Tagged              ⭐ Rated             📤 Exported  │   │
│  │     2,103 (54%)            1,456 (37%)         892       │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─ Recent Activity ────────────────────┐ ┌─ Quick Actions ──┐  │
│  │                                       │ │                  │  │
│  │  [Asset] WSOP_2023_ME_Day1A.mp4      │ │  [+ New Asset]   │  │
│  │  Updated 5 minutes ago                │ │                  │  │
│  │  → 3 new segments tagged              │ │  [🔍 Browse]     │  │
│  │                                       │ │                  │  │
│  │  [Segment] Hellmuth vs Negreanu       │ │  [📊 Reports]    │  │
│  │  Rated 4.5★ • 2 hours ago            │ │                  │  │
│  │  → Hand #142 • Big bluff              │ │  [⚙ Settings]    │  │
│  │                                       │ │                  │  │
│  │  [Export] Top 50 Hands 2023           │ │  [📤 Export]     │  │
│  │  Completed • 1 day ago                │ │                  │  │
│  │  → 50 segments • 4.2GB                │ │                  │  │
│  │                                       │ └──────────────────┘  │
│  │  [View All Activity]                  │                      │
│  └───────────────────────────────────────┘                      │
│                                                                  │
│  ┌─ Storage Overview ───────────────────────────────────────┐   │
│  │  [████████████░░░░░░░░] 58% (4.7TB / 8TB)                │   │
│  │  Raw: 3.2TB • Segments: 1.5TB                            │   │
│  └───────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

**Components**:
- `DashboardLayout` (Container)
- `StatisticsCard` (x6, 2x3 Grid)
- `ActivityFeed` (Timeline component)
- `QuickActionPanel` (Button group)
- `StorageProgressBar` (Linear progress)

---

### 3.2 Asset List (Search & Browse)

```
┌──────────────────────────────────────────────────────────────────┐
│ ☰ Assets                               [Search assets...] 🔔 👤 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ Filters ──────────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  Year: [All ▼]  Event: [All ▼]  Status: [All ▼]           │ │
│  │                                                             │ │
│  │  Tags: [+Add Filter]                                        │ │
│  │  Duration: [── 0h ──────────── 12h+ ──]                    │ │
│  │  Segments: [☑ Has Segments] [☐ No Segments]               │ │
│  │                                                             │ │
│  │  [Clear Filters]                           [Advanced ▼]    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Results: 247 assets  [⊞ Grid] [☰ List]  Sort: [Recent ▼]      │
│                                                                  │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ [Thumbnail]  │ [Thumbnail]  │ [Thumbnail]  │ [Thumbnail]  │  │
│  │  WSOP_2023   │  WSOP_2023   │  WSOP_2023   │  WSOP_2023   │  │
│  │  _ME_Day1A   │  _ME_Day1B   │  _ME_Day2    │  _ME_Day3    │  │
│  │              │              │              │              │  │
│  │  ⏱ 8h 42m    │  ⏱ 9h 15m    │  ⏱ 7h 33m    │  ⏱ 6h 21m    │  │
│  │  🎬 12 seg.  │  🎬 8 seg.   │  🎬 15 seg.  │  🎬 10 seg.  │  │
│  │  🏷 45 tags  │  🏷 32 tags  │  🏷 67 tags  │  🏷 51 tags  │  │
│  │              │              │              │              │  │
│  │  [⋮]         │  [⋮]         │  [⋮]         │  [⋮]         │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                  │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ [Thumbnail]  │ [Thumbnail]  │ [Thumbnail]  │ [Thumbnail]  │  │
│  │  ...         │  ...         │  ...         │  ...         │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                  │
│  [◄] 1 2 3 ... 62 [►]                                           │
│                                                                  │
│  [☑] 4 selected  [📤 Export] [🗑 Delete] [🏷 Tag]               │
└──────────────────────────────────────────────────────────────────┘
```

**Components**:
- `AssetFilterPanel` (Collapsible drawer)
  - `YearSelect` (Dropdown)
  - `EventSelect` (Dropdown with autocomplete)
  - `TagFilter` (Multi-select chips)
  - `DurationSlider` (Range slider)
  - `SegmentToggle` (Checkbox group)
- `AssetGrid` (Responsive grid, 4 columns desktop, 2 tablet, 1 mobile)
- `AssetCard` (Thumbnail, metadata, actions)
- `ViewToggle` (Grid/List button group)
- `BatchActionBar` (Sticky bottom bar)
- `Pagination` (MUI Pagination)

**Search Features**:
```javascript
// Search scope
- Filename (fuzzy match)
- Event name
- Player names (in segments)
- Tags (exact match)
- Date range

// Sort options
- Recent (default)
- Oldest
- Duration (longest/shortest)
- Segments count (most/least)
- Alphabetical (A-Z, Z-A)
```

---

### 3.3 Asset Detail (Segment Timeline)

```
┌──────────────────────────────────────────────────────────────────┐
│ ☰ WSOP_2023_ME_Day1A.mp4               [Search...] 🔔 👤        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ Video Player ─────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │                    [▶ Play/Pause]                           │ │
│  │                                                             │ │
│  │  00:00:00 [═══════════════════════] 08:42:15                │ │
│  │  [Volume] [CC] [Settings] [Fullscreen]                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─ Metadata ──────────────────────────┐ ┌─ Quick Stats ─────┐ │
│  │                                      │ │                   │ │
│  │  File: WSOP_2023_ME_Day1A.mp4       │ │  Segments: 12     │ │
│  │  Event: WSOP 2023 Main Event        │ │  Duration: 8h 42m │ │
│  │  Date: 2023-07-03                   │ │  Tags: 45         │ │
│  │  Resolution: 1920x1080              │ │  Rated: 8/12      │ │
│  │  Size: 18.4GB                       │ │  Exported: 5/12   │ │
│  │                                      │ └───────────────────┘ │
│  │  [Edit Metadata]                     │                       │
│  └──────────────────────────────────────┘                       │
│                                                                  │
│  ┌─ Segment Timeline ──────────────────────────────────────────┐│
│  │                                                              ││
│  │  00:00                  04:00                   08:42       ││
│  │  |══════════════════════════════════════════════════════|   ││
│  │  |██|  |████|   |██|      |███|        |█|    |███|         ││
│  │  #1   #2  #3    #4        #5          #6      #7           ││
│  │                                                              ││
│  │  Zoom: [━━━━━━━━━|━━━] [Fit to View]                        ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─ Segments (12) ──────────────────────── [+ New Segment] ───┐│
│  │                                                              ││
│  │  [Grid] [List]  Filter: [All ▼]  Sort: [Timecode ▼]        ││
│  │                                                              ││
│  │  ┌──────────────────────────────────────────────────────┐   ││
│  │  │ #1  Hand #23 - Ace King vs Queens                    │   ││
│  │  │     00:12:34 → 00:18:45 (6m 11s)                     │   ││
│  │  │     ⭐ 4.5  🏷 bluff, hero-call, tension             │   ││
│  │  │     Players: Phil Hellmuth, Daniel Negreanu          │   ││
│  │  │     [▶ Play] [✎ Edit] [📤 Export] [⋮]               │   ││
│  │  └──────────────────────────────────────────────────────┘   ││
│  │                                                              ││
│  │  ┌──────────────────────────────────────────────────────┐   ││
│  │  │ #2  Hand #45 - Monster Pot                           │   ││
│  │  │     00:23:12 → 00:31:08 (7m 56s)                     │   ││
│  │  │     ⭐ 5.0  🏷 all-in, final-table, epic             │   ││
│  │  │     Players: Phil Ivey, Tom Dwan                     │   ││
│  │  │     [▶ Play] [✎ Edit] [📤 Export] [⋮]               │   ││
│  │  └──────────────────────────────────────────────────────┘   ││
│  │                                                              ││
│  │  [Load More...]                                              ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [← Back to Assets]                   [🗑 Delete Asset]         │
└──────────────────────────────────────────────────────────────────┘
```

**Components**:
- `VideoPlayer` (Custom HTML5 player with timeline markers)
- `MetadataPanel` (Read-only display, edit button)
- `StatsCard` (Summary metrics)
- `SegmentTimeline` (Interactive timeline with zoom/pan)
  - Visual blocks for each segment
  - Color-coded by rating or tags
  - Click to jump to timecode
- `SegmentList` (Virtualized list for performance)
- `SegmentCard` (Expandable card with actions)

**Timeline Interaction**:
```javascript
// User interactions
- Click segment block → Jump to timecode
- Drag segment edge → Adjust boundaries
- Double-click empty space → Create new segment
- Right-click → Context menu (Edit, Delete, Export)
- Scroll wheel → Zoom in/out
- Shift + Drag → Select multiple segments
```

---

### 3.4 Segment Editor (Tagging & Rating)

```
┌──────────────────────────────────────────────────────────────────┐
│ ☰ Edit Segment: Hand #23                      [Save] [Cancel]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ Video Preview ─────────────────────────────────────────────┐│
│  │                                                              ││
│  │                    [▶ Play Preview]                          ││
│  │                                                              ││
│  │  00:12:34 [════════════════] 00:18:45 (6m 11s)               ││
│  │                                                              ││
│  │  ┌─ Timecode Adjustment ──────────────────────────────┐     ││
│  │  │  Start: [00:12:34] [◄] [►]  [Set Current]          │     ││
│  │  │  End:   [00:18:45] [◄] [►]  [Set Current]          │     ││
│  │  │  Duration: 6m 11s                                   │     ││
│  │  └─────────────────────────────────────────────────────┘     ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─ Segment Information ───────────────────────────────────────┐│
│  │                                                              ││
│  │  Title:                                                      ││
│  │  [Hand #23 - Ace King vs Queens                         ]   ││
│  │                                                              ││
│  │  Description:                                                ││
│  │  ┌────────────────────────────────────────────────────┐     ││
│  │  │ Epic hand where Hellmuth bluffs with AK against    │     ││
│  │  │ Negreanu's pocket queens. Amazing read and hero    │     ││
│  │  │ call on the river.                                 │     ││
│  │  └────────────────────────────────────────────────────┘     ││
│  │                                                              ││
│  │  Hand Number: [23    ]  Pot Size: [$1,250,000        ]      ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─ Tagging Interface ─────────────────────────────────────────┐│
│  │                                                              ││
│  │  Tags: [×bluff] [×hero-call] [×tension] [+ Add tag]         ││
│  │                                                              ││
│  │  Suggested:                                                  ││
│  │  [+ all-in] [+ big-pot] [+ final-table] [+ slow-roll]       ││
│  │                                                              ││
│  │  Categories:                                                 ││
│  │  ☑ Action Type    ☐ Tournament Stage    ☐ Player Style      ││
│  │  ☑ Hand Quality   ☑ Emotional Moment    ☐ Strategy          ││
│  │                                                              ││
│  │  Create new tag: [                        ] [Create]        ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─ Players & Rating ──────────────────────────────────────────┐│
│  │                                                              ││
│  │  Players:                                                    ││
│  │  [×Phil Hellmuth] [×Daniel Negreanu] [+ Add player]         ││
│  │                                                              ││
│  │  Hand Rating: ☆☆☆☆☆                                         ││
│  │  [★★★★★] 4.5 / 5.0                                          ││
│  │                                                              ││
│  │  ┌─ Rating Criteria ──────────────────────────────────┐     ││
│  │  │  Action Quality:    [████████░░] 8/10               │     ││
│  │  │  Entertainment:     [█████████░] 9/10               │     ││
│  │  │  Educational Value: [███████░░░] 7/10               │     ││
│  │  │  Rarity:            [██████████] 10/10              │     ││
│  │  └─────────────────────────────────────────────────────┘     ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─ Export Settings ───────────────────────────────────────────┐│
│  │                                                              ││
│  │  Export Status: [Not Exported ▼]                            ││
│  │  Preset: [YouTube Highlight ▼]  [Configure]                 ││
│  │                                                              ││
│  │  ☑ Include intro/outro  ☑ Add watermark  ☐ Burn subtitles  ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [Save Changes]                                 [Delete Segment]│
└──────────────────────────────────────────────────────────────────┘
```

**Components**:
- `SegmentEditorLayout` (Full-screen overlay or side panel)
- `VideoPreview` (Trimmed playback with frame-accurate controls)
- `TimecodeInput` (HH:MM:SS format with validation)
- `TagInput` (Autocomplete with suggestions)
- `TagChip` (Removable chips with category colors)
- `PlayerInput` (Autocomplete from player database)
- `RatingSlider` (Star rating + breakdown)
- `ExportPresetSelector` (Dropdown with custom configurations)
- `ActionButtons` (Primary: Save, Secondary: Delete)

**Tag System**:
```javascript
// Tag categories
Categories = {
  ActionType: [all-in, fold, call, raise, bluff, slowplay],
  HandQuality: [nuts, monster, cooler, bad-beat, suckout],
  TournamentStage: [early, bubble, final-table, heads-up],
  EmotionalMoment: [tension, celebration, tilt, slowroll],
  PlayerStyle: [aggressive, passive, creative, standard],
  Strategy: [value-bet, hero-call, trap, ICM-decision]
}

// Tag autocomplete prioritization
1. Recently used tags
2. Category match (if category selected)
3. Popular tags (usage frequency)
4. Alphabetical
```

---

## 4. Component Specifications (React + MUI)

### 4.1 Core Components

#### `DashboardLayout.tsx`
```typescript
import { Box, Container, AppBar, Drawer } from '@mui/material';

interface DashboardLayoutProps {
  children: React.ReactNode;
  drawerOpen?: boolean;
  onDrawerToggle?: () => void;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  drawerOpen = true,
  onDrawerToggle
}) => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar position="fixed">
        {/* Navigation Bar */}
      </AppBar>

      <Drawer variant="permanent" open={drawerOpen}>
        {/* Sidebar Navigation */}
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Container maxWidth="xl">
          {children}
        </Container>
      </Box>
    </Box>
  );
};
```

#### `AssetCard.tsx`
```typescript
import { Card, CardMedia, CardContent, CardActions, Typography, Chip } from '@mui/material';

interface AssetCardProps {
  asset: {
    id: string;
    filename: string;
    thumbnail: string;
    duration: string;
    segmentCount: number;
    tagCount: number;
  };
  onSelect?: (id: string) => void;
  selected?: boolean;
}

export const AssetCard: React.FC<AssetCardProps> = ({
  asset,
  onSelect,
  selected = false
}) => {
  return (
    <Card
      sx={{
        height: '100%',
        border: selected ? 2 : 0,
        borderColor: 'primary.main'
      }}
      onClick={() => onSelect?.(asset.id)}
    >
      <CardMedia
        component="img"
        height="140"
        image={asset.thumbnail}
        alt={asset.filename}
      />
      <CardContent>
        <Typography variant="body2" noWrap>
          {asset.filename}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
          <Chip icon={<AccessTime />} label={asset.duration} size="small" />
          <Chip icon={<MovieFilter />} label={`${asset.segmentCount} seg.`} size="small" />
          <Chip icon={<LocalOffer />} label={`${asset.tagCount} tags`} size="small" />
        </Box>
      </CardContent>
    </Card>
  );
};
```

#### `SegmentTimeline.tsx`
```typescript
import { Box, Paper, Slider } from '@mui/material';
import { useRef, useState } from 'react';

interface Segment {
  id: string;
  startTime: number;
  endTime: number;
  title: string;
  rating?: number;
}

interface SegmentTimelineProps {
  segments: Segment[];
  duration: number;
  onSegmentClick?: (segment: Segment) => void;
  onSeek?: (time: number) => void;
}

export const SegmentTimeline: React.FC<SegmentTimelineProps> = ({
  segments,
  duration,
  onSegmentClick,
  onSeek
}) => {
  const [zoom, setZoom] = useState(1);
  const timelineRef = useRef<HTMLDivElement>(null);

  const getSegmentPosition = (startTime: number, endTime: number) => ({
    left: `${(startTime / duration) * 100}%`,
    width: `${((endTime - startTime) / duration) * 100}%`
  });

  return (
    <Paper sx={{ p: 2 }}>
      <Box
        ref={timelineRef}
        sx={{
          position: 'relative',
          height: 60,
          background: 'linear-gradient(to right, #f0f0f0, #e0e0e0)',
          borderRadius: 1,
          overflow: 'hidden'
        }}
      >
        {segments.map(segment => (
          <Box
            key={segment.id}
            sx={{
              position: 'absolute',
              ...getSegmentPosition(segment.startTime, segment.endTime),
              height: '100%',
              backgroundColor: getRatingColor(segment.rating),
              cursor: 'pointer',
              '&:hover': { opacity: 0.8 }
            }}
            onClick={() => onSegmentClick?.(segment)}
            title={segment.title}
          />
        ))}
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
        <Typography variant="caption">Zoom:</Typography>
        <Slider
          value={zoom}
          onChange={(_, value) => setZoom(value as number)}
          min={1}
          max={10}
          step={0.5}
          sx={{ width: 200 }}
        />
      </Box>
    </Paper>
  );
};

function getRatingColor(rating?: number): string {
  if (!rating) return '#757575';
  if (rating >= 4.5) return '#4caf50'; // Green
  if (rating >= 3.5) return '#2196f3'; // Blue
  if (rating >= 2.5) return '#ff9800'; // Orange
  return '#f44336'; // Red
}
```

#### `TagInput.tsx`
```typescript
import { Autocomplete, Chip, TextField } from '@mui/material';
import { useState } from 'react';

interface Tag {
  id: string;
  name: string;
  category?: string;
}

interface TagInputProps {
  tags: Tag[];
  suggestions: Tag[];
  onChange: (tags: Tag[]) => void;
}

export const TagInput: React.FC<TagInputProps> = ({
  tags,
  suggestions,
  onChange
}) => {
  const [inputValue, setInputValue] = useState('');

  return (
    <Autocomplete
      multiple
      freeSolo
      options={suggestions}
      value={tags}
      inputValue={inputValue}
      onInputChange={(_, value) => setInputValue(value)}
      onChange={(_, newValue) => {
        const processedTags = newValue.map(v =>
          typeof v === 'string' ? { id: v, name: v } : v
        );
        onChange(processedTags);
      }}
      getOptionLabel={(option) =>
        typeof option === 'string' ? option : option.name
      }
      renderTags={(value, getTagProps) =>
        value.map((option, index) => (
          <Chip
            label={typeof option === 'string' ? option : option.name}
            {...getTagProps({ index })}
            color={getCategoryColor(option.category)}
          />
        ))
      }
      renderInput={(params) => (
        <TextField
          {...params}
          placeholder="Add tags..."
          variant="outlined"
        />
      )}
    />
  );
};
```

### 4.2 Filter Components

#### `AssetFilterPanel.tsx`
```typescript
import { Box, FormControl, Select, Slider, Checkbox, FormControlLabel } from '@mui/material';

interface FilterState {
  year: string[];
  event: string[];
  hasSegments: boolean | null;
  durationRange: [number, number];
  tags: string[];
}

interface AssetFilterPanelProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
}

export const AssetFilterPanel: React.FC<AssetFilterPanelProps> = ({
  filters,
  onChange
}) => {
  return (
    <Box sx={{ p: 2, borderRight: 1, borderColor: 'divider' }}>
      <Typography variant="h6" gutterBottom>Filters</Typography>

      {/* Year Filter */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Year</InputLabel>
        <Select
          multiple
          value={filters.year}
          onChange={(e) => onChange({ ...filters, year: e.target.value })}
        >
          <MenuItem value="2023">2023</MenuItem>
          <MenuItem value="2022">2022</MenuItem>
          <MenuItem value="2021">2021</MenuItem>
        </Select>
      </FormControl>

      {/* Duration Slider */}
      <Typography variant="body2" gutterBottom>Duration</Typography>
      <Slider
        value={filters.durationRange}
        onChange={(_, value) => onChange({
          ...filters,
          durationRange: value as [number, number]
        })}
        valueLabelDisplay="auto"
        min={0}
        max={720} // 12 hours
        marks={[
          { value: 0, label: '0h' },
          { value: 360, label: '6h' },
          { value: 720, label: '12h+' }
        ]}
      />

      {/* Segment Status */}
      <FormControlLabel
        control={
          <Checkbox
            checked={filters.hasSegments === true}
            onChange={(e) => onChange({
              ...filters,
              hasSegments: e.target.checked ? true : null
            })}
          />
        }
        label="Has Segments"
      />
    </Box>
  );
};
```

---

## 5. User Flows

### 5.1 Primary Flow: Browse → View → Edit → Export

```
User Journey: "Find and export epic poker hand"

1. Dashboard → Click "Browse Assets"
   └─ Goal: Access video library

2. Asset List → Apply filters
   ├─ Year: 2023
   ├─ Event: WSOP Main Event
   └─ Tags: "epic", "final-table"
   └─ Result: 12 matching assets

3. Asset Card → Click thumbnail
   └─ Opens: Asset Detail view

4. Asset Detail → View segment timeline
   ├─ Click segment block #7
   └─ Video jumps to 05:23:12

5. Segment Card → Click "Edit"
   └─ Opens: Segment Editor overlay

6. Segment Editor → Adjust rating to 5★
   ├─ Add tags: "all-in", "dramatic"
   ├─ Set export preset: "YouTube Highlight"
   └─ Click "Save"

7. Asset Detail → Segment updated
   └─ Click segment "Export" button

8. Export complete → Notification
   └─ "Segment exported to /exports/epic_hand_7.mp4"
```

### 5.2 Secondary Flow: Batch Tagging

```
User Journey: "Tag multiple segments at once"

1. Asset Detail → Select segment timeline
   ├─ Shift + Click segments #3, #4, #5
   └─ 3 segments selected

2. Batch Action Bar appears
   └─ Click "Tag" button

3. Batch Tag Dialog → Add tags
   ├─ "tournament-final"
   ├─ "high-stakes"
   └─ Click "Apply to 3 segments"

4. Confirmation → All segments updated
   └─ Timeline shows tag indicators
```

---

## 6. Accessibility Features

### 6.1 Keyboard Navigation
```
Global Shortcuts:
- Ctrl + K → Focus search
- Ctrl + F → Open filter panel
- Esc → Close modal/drawer
- Tab → Navigate focusable elements

Video Player:
- Space → Play/Pause
- ← / → → Seek -5s / +5s
- J / L → Frame backward/forward
- M → Mute/Unmute
- F → Fullscreen

Segment Timeline:
- Arrow keys → Navigate segments
- Enter → Open segment editor
- Delete → Delete selected segment
```

### 6.2 Screen Reader Support
```typescript
// Example ARIA labels
<AssetCard
  aria-label={`Video asset ${filename}, duration ${duration}, ${segmentCount} segments`}
  role="article"
/>

<SegmentTimeline
  role="region"
  aria-label="Video segments timeline"
>
  <Box
    role="button"
    aria-label={`Segment ${title}, from ${startTime} to ${endTime}, rated ${rating} stars`}
  />
</SegmentTimeline>

<TagInput
  aria-label="Add tags to segment"
  aria-describedby="tag-helper-text"
/>
```

### 6.3 Color Contrast
All text meets WCAG AA standards:
- Primary text: 14:1 contrast ratio
- Secondary text: 7:1 contrast ratio
- Interactive elements: 4.5:1 minimum

---

## 7. Responsive Design

### 7.1 Breakpoints (MUI Default)
```
xs: 0px (mobile)
sm: 600px (tablet)
md: 900px (desktop)
lg: 1200px (large desktop)
xl: 1536px (extra large)
```

### 7.2 Layout Adaptations

#### Desktop (1200px+)
- Sidebar always visible
- Asset grid: 4 columns
- Segment timeline: Full width with zoom controls
- Video player: 16:9 aspect ratio, max 1280px

#### Tablet (600px - 1199px)
- Collapsible sidebar
- Asset grid: 2 columns
- Segment timeline: Simplified view, no zoom
- Video player: Responsive width

#### Mobile (0 - 599px)
- Bottom navigation bar
- Asset list: 1 column
- Segment timeline: Vertical list (no visual timeline)
- Video player: Full width
- Filter panel: Drawer overlay

```typescript
// Example responsive grid
<Grid container spacing={2}>
  <Grid item xs={12} sm={6} md={4} lg={3}>
    <AssetCard {...props} />
  </Grid>
</Grid>

// Responsive video player
<Box
  sx={{
    width: '100%',
    maxWidth: { xs: '100%', md: 1280 },
    aspectRatio: '16/9'
  }}
>
  <VideoPlayer />
</Box>
```

---

## 8. Performance Optimization

### 8.1 Virtualization
```typescript
// Use react-window for large lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={segments.length}
  itemSize={120}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <SegmentCard segment={segments[index]} />
    </div>
  )}
</FixedSizeList>
```

### 8.2 Lazy Loading
```typescript
// Code splitting
const SegmentEditor = lazy(() => import('./SegmentEditor'));

// Image lazy loading
<CardMedia
  component="img"
  loading="lazy"
  src={thumbnail}
/>
```

### 8.3 Data Caching
```typescript
// React Query for server state
const { data: assets } = useQuery(
  ['assets', filters],
  () => fetchAssets(filters),
  { staleTime: 5 * 60 * 1000 } // 5 minutes
);
```

---

## 9. Design Rationale

### 9.1 Why Timeline-Based UI?
**Problem**: Users need to quickly scan hours of footage for specific moments.

**Solution**: Visual timeline with segment blocks provides:
- Instant overview of content distribution
- Color-coded quality indicators (rating)
- Direct click-to-play navigation
- Spatial memory aids (users remember "that epic hand was in the middle")

### 9.2 Why Inline Editing?
**Problem**: Traditional modal dialogs interrupt workflow and lose context.

**Solution**: Segment editor as overlay panel allows:
- Video preview remains visible during editing
- Quick iterative adjustments without context switching
- Keyboard shortcuts for power users
- Cancel without losing position in timeline

### 9.3 Why Tag Autocomplete?
**Problem**: Free-form tagging leads to inconsistent taxonomy (e.g., "all-in" vs "allin" vs "all in").

**Solution**: Autocomplete with suggestions:
- Enforces consistent vocabulary
- Suggests category-specific tags
- Allows creation of new tags when needed
- Shows tag usage frequency for popular choices

---

## 10. Implementation Notes

### 10.1 Tech Stack
```yaml
Frontend:
  - React 18.x
  - Material-UI (MUI) 5.x
  - React Router 6.x
  - React Query (TanStack Query)
  - Zustand (state management)

Video:
  - video.js or Plyr (HTML5 player)
  - MediaElement.js (frame-accurate seeking)

Build:
  - Vite (fast HMR)
  - TypeScript (type safety)
```

### 10.2 Component Library Structure
```
src/
├── components/
│   ├── layout/
│   │   ├── DashboardLayout.tsx
│   │   ├── AppBar.tsx
│   │   └── Sidebar.tsx
│   ├── assets/
│   │   ├── AssetCard.tsx
│   │   ├── AssetGrid.tsx
│   │   └── AssetFilterPanel.tsx
│   ├── segments/
│   │   ├── SegmentTimeline.tsx
│   │   ├── SegmentCard.tsx
│   │   └── SegmentEditor.tsx
│   ├── video/
│   │   └── VideoPlayer.tsx
│   └── shared/
│       ├── TagInput.tsx
│       ├── RatingInput.tsx
│       └── TimecodeInput.tsx
├── pages/
│   ├── Dashboard.tsx
│   ├── AssetList.tsx
│   └── AssetDetail.tsx
└── hooks/
    ├── useAssets.ts
    ├── useSegments.ts
    └── useTags.ts
```

### 10.3 API Integration Points
```typescript
// Expected API endpoints
interface API {
  assets: {
    list: (filters: FilterState) => Promise<Asset[]>;
    get: (id: string) => Promise<Asset>;
    update: (id: string, data: Partial<Asset>) => Promise<Asset>;
    delete: (id: string) => Promise<void>;
  };
  segments: {
    list: (assetId: string) => Promise<Segment[]>;
    create: (assetId: string, data: SegmentData) => Promise<Segment>;
    update: (id: string, data: Partial<Segment>) => Promise<Segment>;
    delete: (id: string) => Promise<void>;
    export: (id: string, preset: ExportPreset) => Promise<ExportJob>;
  };
  tags: {
    list: () => Promise<Tag[]>;
    suggestions: (query: string, category?: string) => Promise<Tag[]>;
    create: (name: string, category?: string) => Promise<Tag>;
  };
}
```

---

## 11. Next Steps

### 11.1 Prototype Phase
1. Create interactive Figma mockup
2. User testing with poker content editors
3. Validate timeline interaction patterns
4. Test tag autocomplete with real taxonomy

### 11.2 Development Phase
1. Set up React + MUI boilerplate
2. Implement core layout components
3. Build segment timeline with zoom/pan
4. Integrate video player with timecode sync
5. Develop tag system with autocomplete

### 11.3 Testing Phase
1. Unit tests for component logic
2. Integration tests for user flows
3. Accessibility audit (WCAG 2.1 AA)
4. Performance testing with 1000+ assets
5. Cross-browser testing (Chrome, Firefox, Safari, Edge)

---

## Changelog

**v1.0.0** (2025-12-11)
- Initial UI mockup specification
- Complete wireframes for 4 main screens
- Component specifications with TypeScript
- Accessibility and responsive design guidelines
- Implementation roadmap

---

**File**: `D:\AI\claude01\Archive_Converter\docs\UI_MOCKUP.md`
