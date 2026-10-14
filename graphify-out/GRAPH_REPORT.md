# Graph Report - TheLivingCanvas  (2026-10-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3315 nodes · 7076 edges · 150 communities (108 shown, 42 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 286 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `aa8258b4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- PrototypeMuseumBuilder
- addon.py
- museum_lib.py
- BlenderMCPServer
- MuseumSceneBuilder
- Transform
- premium_request
- ._polyhaven_import_texture
- PaintBrushController
- dependencies
- PaintSurface
- museum_int.py
- PlayerInventory
- StudioSceneBuilder
- CollectionSet
- drapes
- furnish
- unityengine
- museum_garden.py
- make_texture_templates.py
- B
- tube
- GalleryFrame
- wing
- PaintingPlot
- manifest.json
- dependencies
- packages-lock.json
- generate_embers.py
- template_pack/spec.py
- com.unity.mathematics
- com.unity.modules.jsonserialize
- loft
- generate_sfx.py
- Npc
- make_pack.py
- com.unity.modules.imgui
- rbox
- PaintTemplateGenerator
- CanvasType
- StyleDefinition
- SaveRegistry
- PaintToolsUI
- system_collections_generic
- CalendarUI
- com.unity.modules.audio
- generate_soundtrack.py
- ShopOffer
- CameraModeController
- com.unity.modules.unitywebrequest
- com.unity.render-pipelines.core
- TheLivingCanvas.Data
- CropPlant
- PaintingItem
- CanvasInteractable
- SeasonClock
- ShopUI
- PigmentDefinition
- CropDefinition
- CommissionDefinition
- PaintTemplate
- SaveData
- SeasonVisuals
- validate_soundtrack.py
- dependencies
- system
- SfxPlayer
- InventoryUI
- _polyhaven_api_get
- make_prototype_textures.py
- TheLivingCanvas.Interaction
- PaintingPlacer
- com.unity.modules.physics
- PlayerInteractor
- CropPickerUI
- TutorialObjectives
- museum_ext.py
- UserEditRecorder
- PaintHistory
- SaveManager
- MonoBehaviour
- ModalPanel
- MortarUI
- com.unity.modules.ui
- StudioSceneBuilder.cs
- PauseMenu
- BrushDefinition
- PaintBurst
- CoverageReadoutUI
- com.unity.test-framework
- Sh
- Mutation
- PigmentOffer
- GlowbellPlant
- ArtistLevel
- DayLighting
- com.unity.modules.uielements
- _register_edit_capture_handlers
- ISaveable
- GardenGate
- ._execute_command_internal
- main
- window
- benches_and_lamps
- facade_details
- .TryOpen
- CropItem
- com.unity.ext.nunit
- CursorLock
- com.unity.ai.navigation
- CommissionBoard
- FestivalStand
- WallCalendar
- com.unity.modules.physics2d
- com.unity.ugui
- .search_polypizza_models
- MusicPlayer
- PaintTool
- SunbellPlant
- HeldBrush
- vegetation
- entrance
- CoinCounterUI
- PaintFeedbackUI
- DayFadeUI
- pathlib
- build_xml
- build_midi
- D
- Face
- GameSettings
- Rarity
- SketchOffer
- TomatoPlant
- .pick_viewport_object
- UiScaleApplier
- CanvasUpgradeOffer
- .Measure
- LevelCounterUI
- com.unity.modules.wind
- .download_polypizza_model
- hall_rug
- placeholder
- premium_enabled_generators

## God Nodes (most connected - your core abstractions)
1. `StudioSceneBuilder` - 103 edges
2. `PaintBrushController` - 103 edges
3. `BlenderMCPServer` - 80 edges
4. `CropDefinition` - 64 edges
5. `PaintSurface` - 59 edges
6. `SeasonClock` - 53 edges
7. `ArtistLevel` - 51 edges
8. `furnish()` - 51 edges
9. `PlayerInventory` - 50 edges
10. `CanvasInteractable` - 47 edges

## Surprising Connections (you probably didn't know these)
- `HB` --uses--> `B`  [INFERRED]
  Tools/museum_models/museum_int.py → Tools/museum_models/museum_lib.py
- `UV en metros: cada cara se proyecta sobre el plano de su normal dominante (1…` --rationale_for--> `planar_uv()`  [EXTRACTED]
  Tools/template_pack/build_blend.py → ArtSource/Pack/TheLivingCanvas_ArtTemplates/blender/scripts/build_blend.py
- `Casa: cuerpo + tejado a dos aguas + puerta + ventanas. door/wins: (z, y,…` --rationale_for--> `house()`  [EXTRACTED]
  Tools/template_pack/spec.py → ArtSource/Pack/TheLivingCanvas_ArtTemplates/blender/scripts/spec.py
- `CanvasGuide` --references--> `PaintSurface`  [EXTRACTED]
  Assets/_TheLivingCanvas/Scripts/Painting/CanvasGuide.cs → Assets/_TheLivingCanvas/Scripts/Painting/PaintSurface.cs
- `CanvasInteractable` --references--> `PaintSurface`  [EXTRACTED]
  Assets/_TheLivingCanvas/Scripts/Painting/CanvasInteractable.cs → Assets/_TheLivingCanvas/Scripts/Painting/PaintSurface.cs

## Import Cycles
- None detected.

## Communities (150 total, 42 thin omitted)

### Community 0 - "PrototypeMuseumBuilder"
Cohesion: 0.05
Nodes (5): PrototypeMeshes, PrototypeMuseumBuilder, PainterlyDescolor, Amount, PrototypeViewer

### Community 1 - "addon.py"
Cohesion: 0.04
Nodes (34): addon_release_key(), _addon_update_check_on_startup(), addon_version_label(), _blendermcp_ensure_server_running(), _blendermcp_load_post(), BLENDERMCP_OT_CheckAddonUpdate, BLENDERMCP_OT_OpenTerms, BLENDERMCP_OT_StartServer (+26 more)

### Community 2 - "museum_lib.py"
Cohesion: 0.05
Nodes (31): add_label(), axis_z_to_y(), build_bm(), build_file(), get_material(), hex_color(), make_part(), part_extent_x() (+23 more)

### Community 3 - "BlenderMCPServer"
Cohesion: 0.05
Nodes (4): BlenderMCPServer, get_all_mesh_children(), hunyuan_api_profile(), premium_active()

### Community 4 - "MuseumSceneBuilder"
Cohesion: 0.05
Nodes (8): LightEntry, LightFile, MuseumSceneBuilder, AreaDoor, CanInteract, Prompt, AreaTransition, Busy

### Community 5 - "Transform"
Cohesion: 0.12
Nodes (4): PaintingFinisher, PaintModeController, ActiveCanvas, IsPainting

### Community 6 - "premium_request"
Cohesion: 0.05
Nodes (36): BLENDERMCP_AddonPreferences, BLENDERMCP_OT_PremiumActivate, BLENDERMCP_OT_PremiumDeactivate, BLENDERMCP_OT_PremiumOpenAccount, BLENDERMCP_OT_PremiumRefresh, BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey, BLENDERMCP_PT_Panel, get_blendermcp_addon_preferences() (+28 more)

### Community 7 - "._polyhaven_import_texture"
Cohesion: 0.06
Nodes (17): _polyhaven_asset_record(), _polyhaven_asset_url(), _polyhaven_authors(), _polyhaven_available(), _polyhaven_blend_version(), _polyhaven_dimensions_mm(), _polyhaven_download(), _polyhaven_mapping_node() (+9 more)

### Community 8 - "PaintBrushController"
Cohesion: 0.05
Nodes (21): PaintBrushController, ActiveSurface, Brushes, BrushRadius, CanRedo, CanUndo, EraserActive, EyedropperActive (+13 more)

### Community 9 - "dependencies"
Cohesion: 0.04
Nodes (49): dependencies, com.coplaydev.unity-mcp, com.unity.ai.navigation, com.unity.cinemachine, com.unity.collab-proxy, com.unity.ide.rider, com.unity.ide.visualstudio, com.unity.inputsystem (+41 more)

### Community 10 - "PaintSurface"
Cohesion: 0.08
Nodes (12): PaintSurface, BaseColor, CanRedo, CanUndo, Height, LongStrokeShare, Pixels, PixelWorldSize (+4 more)

### Community 11 - "museum_int.py"
Cohesion: 0.08
Nodes (26): body(), annex_shell(), build(), build_open(), _bvh(), door_casings(), fz(), gallery_tracks() (+18 more)

### Community 12 - "PlayerInventory"
Cohesion: 0.09
Nodes (9): ListPanel, SellCrate, CanInteract, Prompt, Wallet, Coins, PlayerInventory, Items (+1 more)

### Community 13 - "StudioSceneBuilder"
Cohesion: 0.14
Nodes (3): StudioSceneBuilder, CropVariant, ZoneRequirement

### Community 14 - "CollectionSet"
Cohesion: 0.09
Nodes (14): CollectionEntry, CollectionSet, DisplayName, Id, RewardCoins, RewardPigment, RewardPigmentAmount, RewardText (+6 more)

### Community 15 - "drapes"
Cohesion: 0.07
Nodes (20): _az(), band_loop(), bezier(), blade3d(), keep(), drapes(), prof(), _ficus_leaf() (+12 more)

### Community 16 - "furnish"
Cohesion: 0.05
Nodes (19): broom(), coat_hook(), directory_board(), dustpan(), furnish(), vase(), hand_dryer(), key_cabinet() (+11 more)

### Community 17 - "unityengine"
Cohesion: 0.11
Nodes (5): TheLivingCanvas.Tutorial, TheLivingCanvas.Economy, TheLivingCanvas.Growth, TheLivingCanvas.Painting, TheLivingCanvas.Feedback

### Community 18 - "museum_garden.py"
Cohesion: 0.07
Nodes (18): _basis(), flower_head(), flower_patch(), geranium(), gothic_gate(), meadow_flower(), palette_outline(), palette_shape() (+10 more)

### Community 19 - "make_texture_templates.py"
Cohesion: 0.10
Nodes (28): blob(), chaikin(), circle(), cloud(), curve(), f_ceramic(), f_flag(), f_gilded() (+20 more)

### Community 20 - "B"
Cohesion: 0.06
Nodes (8): curtain_span(), LB, radiator(), room_at(), WB, windows_int(), B, warp()

### Community 21 - "tube"
Cohesion: 0.07
Nodes (18): ceilings_and_lights(), chandelier(), arm(), dome_light(), fluorescent(), lid(), lantern(), frame() (+10 more)

### Community 22 - "GalleryFrame"
Cohesion: 0.07
Nodes (12): GalleryFrame, CanInteract, Painting, Prompt, GalleryHangUI, InventoryItem, Detail, DisplayName (+4 more)

### Community 23 - "wing"
Cohesion: 0.09
Nodes (21): art_slot(), fn(), door_leaf(), fn(), hatch(), HB, pictogram_fig(), poly() (+13 more)

### Community 24 - "PaintingPlot"
Cohesion: 0.09
Nodes (10): PaintingPlot, CanInteract, GrowthProgress, Harvested, HarvestName, InSeason, Painting, Prompt (+2 more)

### Community 25 - "manifest.json"
Cohesion: 0.06
Nodes (31): com.unity.modules.imgui, com.unity.modules.jsonserialize, com.unity.modules.physics, com.unity.modules.unitywebrequest, com.coplaydev.unity-mcp, com.unity.ai.navigation, com.unity.cinemachine, com.unity.collab-proxy (+23 more)

### Community 26 - "dependencies"
Cohesion: 0.06
Nodes (32): dependencies, depth, hash, source, version, dependencies, depth, source (+24 more)

### Community 27 - "packages-lock.json"
Cohesion: 0.06
Nodes (30): com.unity.modules.ai, com.unity.modules.animation, com.unity.modules.assetbundle, com.unity.modules.audio, com.unity.modules.director, com.unity.modules.imageconversion, com.unity.modules.particlesystem, com.unity.modules.physics2d (+22 more)

### Community 28 - "generate_embers.py"
Cohesion: 0.17
Nodes (26): add(), add_rest(), bass_note(), chords_of(), compose(), default_artic(), fifth_low(), fill_rests() (+18 more)

### Community 29 - "template_pack/spec.py"
Cohesion: 0.12
Nodes (22): B(), C(), fence_section(), frame_wall(), G(), glowbell(), house(), Q() (+14 more)

### Community 30 - "com.unity.mathematics"
Cohesion: 0.07
Nodes (30): dependencies, depth, source, url, version, dependencies, depth, source (+22 more)

### Community 31 - "com.unity.modules.jsonserialize"
Cohesion: 0.07
Nodes (30): dependencies, depth, source, version, dependencies, depth, source, version (+22 more)

### Community 32 - "loft"
Cohesion: 0.08
Nodes (15): _axis_xf(), bottle(), cleaning_cart(), cloth(), finial(), jug(), loft(), product_shelf() (+7 more)

### Community 33 - "generate_sfx.py"
Cohesion: 0.12
Nodes (14): bell(), brush_loop(), coin(), envelope(), harvest(), level_up(), lowpass(), mix() (+6 more)

### Community 34 - "Npc"
Cohesion: 0.09
Nodes (6): CommissionRewards, DialogueUI, Npc, CanInteract, Current, Prompt

### Community 35 - "make_pack.py"
Cohesion: 0.14
Nodes (20): arrow(), guide_common(), make_guides(), new_layer(), silhouette_guide(), write_ora(), guide_canvas(), make_guide() (+12 more)

### Community 36 - "com.unity.modules.imgui"
Cohesion: 0.07
Nodes (29): dependencies, depth, source, url, version, dependencies, depth, source (+21 more)

### Community 38 - "rbox"
Cohesion: 0.08
Nodes (14): bench_gallery(), bench_modern(), cat_sculpture(), sculpt_a(), pedal_bin(), rbox(), rrect(), sculpt_arch() (+6 more)

### Community 40 - "CanvasType"
Cohesion: 0.09
Nodes (17): CanvasType, Description, DisplayName, HarvestMultiplier, Id, PigmentMultiplier, PlotScale, ScoreBonus (+9 more)

### Community 41 - "StyleDefinition"
Cohesion: 0.09
Nodes (17): StyleDefinition, Description, DisplayName, GrowthMultiplier, Id, Kind, Pastel, PigmentMultiplier (+9 more)

### Community 42 - "SaveRegistry"
Cohesion: 0.16
Nodes (3): PaintingStore, Folder, SaveRegistry

### Community 44 - "system_collections_generic"
Cohesion: 0.18
Nodes (3): TheLivingCanvas.Gallery, TheLivingCanvas.Core, TheLivingCanvas.Progression

### Community 45 - "CalendarUI"
Cohesion: 0.12
Nodes (3): CalendarEvents, CalendarUI, Cell

### Community 46 - "com.unity.modules.audio"
Cohesion: 0.08
Nodes (26): dependencies, depth, source, version, dependencies, depth, source, version (+18 more)

### Community 47 - "generate_soundtrack.py"
Cohesion: 0.14
Nodes (18): Acc, add_direction(), build_midi(), setup(), build_notes(), build_xml(), down_octave(), dyn_at() (+10 more)

### Community 48 - "ShopOffer"
Cohesion: 0.10
Nodes (12): ShopOffer, Description, DisplayName, HalfPriceOnMarketDay, Icon, Price, RequiredLevel, Season (+4 more)

### Community 49 - "CameraModeController"
Cohesion: 0.11
Nodes (5): CameraMode, FirstPerson, FixedView, CameraModeController, Mode

### Community 50 - "com.unity.modules.unitywebrequest"
Cohesion: 0.09
Nodes (25): dependencies, depth, source, version, dependencies, depth, source, version (+17 more)

### Community 51 - "com.unity.render-pipelines.core"
Cohesion: 0.09
Nodes (25): depth, source, version, dependencies, depth, source, version, dependencies (+17 more)

### Community 52 - "TheLivingCanvas.Data"
Cohesion: 0.14
Nodes (4): TheLivingCanvas.Inventory, TheLivingCanvas.Save, TheLivingCanvas.Data, TheLivingCanvas.Npcs

### Community 53 - "CropPlant"
Cohesion: 0.16
Nodes (7): CropPlant, IsGrown, Progress, StartProgress, PaintingResult, ZoneResult, Passed

### Community 54 - "PaintingItem"
Cohesion: 0.10
Nodes (17): PaintingItem, CanvasType, Crop, CropName, Detail, DisplayName, Generation, Icon (+9 more)

### Community 55 - "CanvasInteractable"
Cohesion: 0.11
Nodes (11): CanvasInteractable, CanInteract, CanvasResolution, CanvasType, Crop, Guide, IsFinished, Prompt (+3 more)

### Community 56 - "SeasonClock"
Cohesion: 0.12
Nodes (11): SeasonClock, Current, Day, DaysPerSeason, FestivalDay, IsFestival, IsMarketDay, MinutesOfDay (+3 more)

### Community 57 - "ShopUI"
Cohesion: 0.13
Nodes (4): ShopStall, CanInteract, Prompt, ShopUI

### Community 58 - "PigmentDefinition"
Cohesion: 0.15
Nodes (6): PigmentDefinition, Color, DisplayName, Id, PigmentStock, StartingAmount

### Community 59 - "CropDefinition"
Cohesion: 0.10
Nodes (14): CropCross, CropDefinition, Crosses, DisplayName, FavoriteSeason, GrowthDuration, Icon, Id (+6 more)

### Community 60 - "CommissionDefinition"
Cohesion: 0.10
Nodes (17): CommissionDefinition, Crop, MinQuality, RequestLines, RequiredPigment, RewardCoins, RewardPigment, RewardPigmentAmount (+9 more)

### Community 61 - "PaintTemplate"
Cohesion: 0.14
Nodes (5): PaintTemplate, DisplayName, Zones, CanvasGuide, PaintEvaluator

### Community 62 - "SaveData"
Cohesion: 0.19
Nodes (9): AmountEntry, EaselSave, FrameSave, ItemSave, NpcSave, PaintingSave, PlotSave, SaveData (+1 more)

### Community 63 - "SeasonVisuals"
Cohesion: 0.16
Nodes (6): Look, SeasonVisuals, SunColor, SunIntensity, SunMiddayElevation, Target

### Community 64 - "validate_soundtrack.py"
Cohesion: 0.13
Nodes (8): check(), midi_notes(), parse_midi(), read_vlq(), check(), midi_notes(), parse_midi(), read_vlq()

### Community 65 - "dependencies"
Cohesion: 0.09
Nodes (22): dependencies, depth, source, url, version, dependencies, depth, source (+14 more)

### Community 66 - "system"
Cohesion: 0.11
Nodes (6): ZoneChannel, Blue, Green, Red, TheLivingCanvas.Audio, TheLivingCanvas.Seasons

### Community 67 - "SfxPlayer"
Cohesion: 0.13
Nodes (9): Sfx, Coin, Harvest, LevelUp, PaintFinish, Place, UiClose, UiOpen (+1 more)

### Community 69 - "_polyhaven_api_get"
Cohesion: 0.10
Nodes (8): _polyhaven_api_get(), _polyhaven_cache_key(), _polyhaven_cache_touch(), _polyhaven_category_paths(), _polyhaven_keyword_match(), _polyhaven_search(), _polyhaven_taxonomy(), PolyHavenAPIError

### Community 70 - "make_prototype_textures.py"
Cohesion: 0.22
Nodes (13): Canvas, half_width_uv(), main(), mix(), shape(), tex_brush(), tex_leaf(), tex_painting() (+5 more)

### Community 73 - "com.unity.modules.physics"
Cohesion: 0.10
Nodes (20): dependencies, depth, source, version, dependencies, depth, source, version (+12 more)

### Community 74 - "PlayerInteractor"
Cohesion: 0.13
Nodes (6): IInteractable, CanInteract, Prompt, PlayerInteractor, Current, InteractAction

### Community 77 - "museum_ext.py"
Cohesion: 0.15
Nodes (10): awning(), build(), cull_hidden(), dormers(), ground(), plant_tuft(), presentation(), roof() (+2 more)

### Community 80 - "PaintHistory"
Cohesion: 0.18
Nodes (3): PaintHistory, CanRedo, CanUndo

### Community 82 - "MonoBehaviour"
Cohesion: 0.12
Nodes (3): FitToScreenHeight, InteractionPromptUI, NightLamp

### Community 84 - "MortarUI"
Cohesion: 0.15
Nodes (4): MortarStation, CanInteract, Prompt, MortarUI

### Community 85 - "com.unity.modules.ui"
Cohesion: 0.12
Nodes (17): dependencies, depth, source, version, dependencies, depth, source, version (+9 more)

### Community 88 - "BrushDefinition"
Cohesion: 0.15
Nodes (9): BrushDefinition, DisplayName, Id, Kind, BrushKind, Fill, Glaze, Round (+1 more)

### Community 90 - "CoverageReadoutUI"
Cohesion: 0.17
Nodes (3): CoverageReadoutUI, CoverageResult, PaintCoverage

### Community 91 - "com.unity.test-framework"
Cohesion: 0.12
Nodes (16): dependencies, depth, source, url, version, depth, dependencies, depth (+8 more)

### Community 92 - "Sh"
Cohesion: 0.12
Nodes (3): arc_band(), reception_desk(), Sh

### Community 93 - "Mutation"
Cohesion: 0.18
Nodes (11): Mutation, Giant, Luminous, None, Twin, Mutations, PaintingQuality, Excellent (+3 more)

### Community 94 - "PigmentOffer"
Cohesion: 0.15
Nodes (6): PigmentOffer, HalfPriceOnMarketDay, Icon, Pigment, Units, RefillOffer

### Community 96 - "ArtistLevel"
Cohesion: 0.16
Nodes (8): ArtistLevel, IsMaxLevel, Level, MaxLevel, NextLevelXp, Progress, Xp, XpGain

### Community 97 - "DayLighting"
Cohesion: 0.21
Nodes (3): DayLighting, LampFactor, Key

### Community 98 - "com.unity.modules.uielements"
Cohesion: 0.13
Nodes (15): dependencies, depth, source, url, version, depth, source, version (+7 more)

### Community 99 - "_register_edit_capture_handlers"
Cohesion: 0.20
Nodes (7): _blendermcp_depsgraph_post(), _blendermcp_redo_post(), _blendermcp_undo_post(), _register_edit_capture_handlers(), sync_edit_capture_handlers(), _telemetry_consent_enabled(), _unregister_edit_capture_handlers()

### Community 101 - "GardenGate"
Cohesion: 0.18
Nodes (3): GardenGate, CanInteract, Prompt

### Community 103 - "main"
Cohesion: 0.15
Nodes (10): balanced(), emit(), fit_lines(), hex2rgb(), main(), nearest_type(), parse_slots(), slots_text() (+2 more)

### Community 104 - "window"
Cohesion: 0.19
Nodes (8): arch_pts(), arch_rise(), arch_spandrels(), is_arched(), louvered_shutter(), sash(), voussoirs(), window()

### Community 105 - "benches_and_lamps"
Cohesion: 0.17
Nodes (7): benches_and_lamps(), dab_flower(), stone_fence(), leaves(), leaf(), top(), to_col()

### Community 106 - "facade_details"
Cohesion: 0.18
Nodes (8): facade_details(), crates(), crate(), P(), ivy_column(), ivy_leaf(), ivy_wall(), window_box()

### Community 108 - "CropItem"
Cohesion: 0.17
Nodes (11): CropItem, Crop, Detail, DisplayName, GrindPigment, Icon, Rarity, StackKey (+3 more)

### Community 109 - "com.unity.ext.nunit"
Cohesion: 0.17
Nodes (12): dependencies, depth, source, version, dependencies, depth, source, url (+4 more)

### Community 112 - "com.unity.ai.navigation"
Cohesion: 0.18
Nodes (11): dependencies, depth, source, url, version, dependencies, depth, source (+3 more)

### Community 113 - "CommissionBoard"
Cohesion: 0.27
Nodes (4): CommissionBoard, CanInteract, Current, Prompt

### Community 114 - "FestivalStand"
Cohesion: 0.22
Nodes (3): FestivalStand, CanInteract, Prompt

### Community 115 - "WallCalendar"
Cohesion: 0.27
Nodes (3): WallCalendar, CanInteract, Prompt

### Community 116 - "com.unity.modules.physics2d"
Cohesion: 0.20
Nodes (10): dependencies, depth, source, version, dependencies, depth, source, version (+2 more)

### Community 117 - "com.unity.ugui"
Cohesion: 0.20
Nodes (10): depth, source, version, dependencies, depth, source, url, version (+2 more)

### Community 118 - ".search_polypizza_models"
Cohesion: 0.20
Nodes (4): _polypizza_category_id(), _polypizza_filter_params(), _polypizza_licence_id(), _polypizza_summarize_model()

### Community 120 - "PaintTool"
Cohesion: 0.28
Nodes (4): ToolOffer, PaintTool, Eyedropper, Symmetry

### Community 123 - "vegetation"
Cohesion: 0.22
Nodes (5): bush(), cypress(), free_spot(), grass_tuft(), vegetation()

### Community 124 - "entrance"
Cohesion: 0.25
Nodes (5): door(), entrance(), faces(), oculus(), stone_steps()

### Community 129 - "build_xml"
Cohesion: 0.36
Nodes (6): Acc, add_direction(), build_xml(), chord_label(), el(), write_note()

### Community 130 - "build_midi"
Cohesion: 0.32
Nodes (8): build_midi(), setup(), dyn_at(), main(), meta(), track_bytes(), vel_at(), vlq()

### Community 133 - "GameSettings"
Cohesion: 0.29
Nodes (5): GameSettings, Fullscreen, Sensitivity, UiScale, Volume

### Community 135 - "Rarity"
Cohesion: 0.33
Nodes (5): Rarity, Common, Rare, Uncommon, RarityExtensions

### Community 144 - "com.unity.modules.wind"
Cohesion: 0.40
Nodes (5): dependencies, depth, source, version, com.unity.modules.wind

### Community 146 - "hall_rug"
Cohesion: 0.50
Nodes (3): hall_rug(), frame(), rect()

### Community 147 - "placeholder"
Cohesion: 0.50
Nodes (3): placeholder(), disc(), poly()

## Knowledge Gaps
- **589 isolated node(s):** `LightEntry`, `Amount`, `BaseColor`, `CanRedo`, `CanUndo` (+584 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 1398 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **42 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PaintBrushController` connect `PaintBrushController` to `Transform`, `PaintSurface`, `PlayerInventory`, `StudioSceneBuilder`, `CollectionSet`, `Npc`, `.CreatePart`, `SaveRegistry`, `PaintToolsUI`, `system_collections_generic`, `CanvasInteractable`, `PigmentDefinition`, `InventoryUI`, `.Build`, `PaintHistory`, `MonoBehaviour`, `MortarUI`, `BrushDefinition`, `CoverageReadoutUI`, `PigmentOffer`, `ISaveable`, `CommissionBoard`, `FestivalStand`, `PaintTool`, `HeldBrush`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `BlenderMCPServer` connect `BlenderMCPServer` to `addon.py`, `_register_edit_capture_handlers`, `_polyhaven_api_get`, `._execute_command_internal`, `._polyhaven_import_texture`, `.describe_node_type`, `.pick_viewport_object`, `.get_world_state_snapshot`, `.download_polypizza_model`, `premium_enabled_generators`, `.search_polypizza_models`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `StudioSceneBuilder` connect `StudioSceneBuilder` to `Transform`, `.CreatePart`, `PlayerInventory`, `CollectionSet`, `.Build`, `CursorLock`, `StudioSceneBuilder.cs`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `LightEntry`, `Amount`, `BaseColor` to the rest of the system?**
  _589 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `PrototypeMuseumBuilder` be split into smaller, more focused modules?**
  _Cohesion score 0.05403348554033485 - nodes in this community are weakly interconnected._
- **Should `addon.py` be split into smaller, more focused modules?**
  _Cohesion score 0.04265593561368209 - nodes in this community are weakly interconnected._
- **Should `museum_lib.py` be split into smaller, more focused modules?**
  _Cohesion score 0.051360842844600525 - nodes in this community are weakly interconnected._