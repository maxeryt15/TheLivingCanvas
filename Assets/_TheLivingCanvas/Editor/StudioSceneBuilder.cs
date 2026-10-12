using System.Collections.Generic;
using System.IO;
using System.Linq;
using TheLivingCanvas.Audio;
using TheLivingCanvas.Core;
using TheLivingCanvas.Data;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Feedback;
using TheLivingCanvas.Gallery;
using TheLivingCanvas.Growth;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Npcs;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Player;
using TheLivingCanvas.Progression;
using TheLivingCanvas.Save;
using TheLivingCanvas.Seasons;
using TheLivingCanvas.Tutorial;
using Unity.Cinemachine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.UI;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UI;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Genera la escena Studio (vertical slice) con placeholders: suelo, paredes,
    /// luz cálida, cámara y post-processing. Es idempotente: se puede volver a ejecutar.
    /// Menú: TheLivingCanvas/Build Studio Scene. Batchmode: -executeMethod TheLivingCanvas.EditorTools.StudioSceneBuilder.Build
    /// </summary>
    public static class StudioSceneBuilder
    {
        const string Root = "Assets/_TheLivingCanvas";
        const string ScenePath = Root + "/Scenes/Studio.unity";
        const string MaterialsFolder = Root + "/Art/Materials";
        const string ProfilePath = Root + "/Settings/StudioVolumeProfile.asset";
        const string StudioZoneProfilePath = Root + "/Settings/StudioZoneVolumeProfile.asset";
        const string GalleryZoneProfilePath = Root + "/Settings/GalleryZoneVolumeProfile.asset";
        const float GlobalTemperature = 12f;
        const float GlobalSaturation = 10f;
        const string ControlsPath = Root + "/Settings/PlayerControls.inputactions";
        const string PlayerPrefabPath = Root + "/Prefabs/Player/Player.prefab";
        const string EaselPrefabPath = Root + "/Prefabs/Canvas/Easel.prefab";
        const string PaintingPlotPrefabPath = Root + "/Prefabs/Crops/PaintingPlot.prefab";
        const string SunflowerPrefabPath = Root + "/Prefabs/Crops/Sunflower.prefab";
        const string TomatoPrefabPath = Root + "/Prefabs/Crops/Tomato.prefab";
        const string GlowbellPrefabPath = Root + "/Prefabs/Crops/Glowbell.prefab";
        const string SunbellPrefabPath = Root + "/Prefabs/Crops/Sunbell.prefab";

        [MenuItem("TheLivingCanvas/Build Studio Scene")]
        public static void Build()
        {
            // Studio.unity se sobrescribe entero, así que solo se pregunta por cambios en otras escenas.
            if (!Application.isBatchMode && HasOtherModifiedScenes() && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
                return;

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var floorMat = GetOrCreateMaterial("M_Floor_Wood", new Color(0.55f, 0.38f, 0.24f));
            var wallMat = GetOrCreateMaterial("M_Wall_Cream", new Color(0.93f, 0.87f, 0.76f));
            var accentMat = GetOrCreateMaterial("M_Accent_Terracotta", new Color(0.80f, 0.45f, 0.30f));

            // Entorno: un estudio abierto por dos lados para que la cámara en 3ª persona vea bien.
            var environment = new GameObject("Environment");
            CreateBlock("Floor", environment.transform, new Vector3(0f, -0.1f, 0f), new Vector3(12f, 0.2f, 12f), floorMat);
            // Pared del fondo con un vano de 2 m x 2,4 m en x = 0: da paso a la galería.
            CreateBlock("Wall_Back_Left", environment.transform, new Vector3(-3.5f, 1.5f, 6f), new Vector3(5f, 3f, 0.2f), wallMat);
            CreateBlock("Wall_Back_Right", environment.transform, new Vector3(3.5f, 1.5f, 6f), new Vector3(5f, 3f, 0.2f), wallMat);
            CreateBlock("Wall_Back_Lintel", environment.transform, new Vector3(0f, 2.7f, 6f), new Vector3(2f, 0.6f, 0.2f), wallMat);
            CreateBlock("Wall_Left", environment.transform, new Vector3(-6f, 1.5f, 0f), new Vector3(0.2f, 3f, 12f), wallMat);
            CreateBlock("Table", environment.transform, new Vector3(-4.5f, 0.4f, 4.5f), new Vector3(2f, 0.8f, 1f), accentMat);

            // Límites invisibles en los lados abiertos para no caerse del suelo.
            // El frente deja un hueco de 3 m (x -1,5..1,5) para salir al pueblo.
            CreateBoundary("Boundary_Front_Left", environment.transform, new Vector3(-3.75f, 1.5f, -6f), new Vector3(4.5f, 3f, 0.2f));
            CreateBoundary("Boundary_Front_Right", environment.transform, new Vector3(3.75f, 1.5f, -6f), new Vector3(4.5f, 3f, 0.2f));
            // El lado derecho deja un hueco de 2 m en z = 0: lo cierra la puerta del jardín.
            CreateBoundary("Boundary_Right_Front", environment.transform, new Vector3(6f, 1.5f, -3.5f), new Vector3(0.2f, 3f, 5f));
            CreateBoundary("Boundary_Right_Back", environment.transform, new Vector3(6f, 1.5f, 3.5f), new Vector3(0.2f, 3f, 5f));

            // Luz cálida de media tarde.
            var sunGo = new GameObject("Sun");
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.92f, 0.80f); // = Spring (SeasonVisuals)
            sun.intensity = 1.5f;
            sun.shadows = LightShadows.Soft;
            sunGo.transform.rotation = Quaternion.Euler(45f, -35f, 0f);

            var seasons = new GameObject("Seasons");
            var seasonClock = seasons.AddComponent<SeasonClock>();
            var seasonVisuals = seasons.AddComponent<SeasonVisuals>();
            var visualsSo = new SerializedObject(seasonVisuals);
            visualsSo.FindProperty("clock").objectReferenceValue = seasonClock;
            SetMaterials(visualsSo.FindProperty("foliageMaterials"),
                GetOrCreateMaterial("M_Garden_Bush", new Color(0.24f, 0.45f, 0.22f)));
            SetMaterials(visualsSo.FindProperty("groundMaterials"),
                GetOrCreateMaterial("M_Grass", new Color(0.42f, 0.62f, 0.30f)),
                GetOrCreateMaterial("M_Town_Grass", new Color(0.40f, 0.47f, 0.35f)));
            visualsSo.ApplyModifiedPropertiesWithoutUndo();

            // DayLighting lee SeasonVisuals y escribe el sol; va justo detrás, antes de cualquier farol que lo lea.
            var dayLighting = seasons.AddComponent<DayLighting>();
            var dayLightingSo = new SerializedObject(dayLighting);
            dayLightingSo.FindProperty("clock").objectReferenceValue = seasonClock;
            dayLightingSo.FindProperty("seasonVisuals").objectReferenceValue = seasonVisuals;
            dayLightingSo.FindProperty("sun").objectReferenceValue = sun;
            dayLightingSo.ApplyModifiedPropertiesWithoutUndo();

            RenderSettings.sun = sun;
            RenderSettings.skybox = AssetDatabase.GetBuiltinExtraResource<Material>("Default-Skybox.mat");
            // Ambiente y niebla de pleno día para la escena en edición; en juego los lleva DayLighting.
            var midday = dayLighting.Evaluate(12f);
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = midday.ambientSky;
            RenderSettings.ambientEquatorColor = midday.ambientEquator;
            RenderSettings.ambientGroundColor = midday.ambientGround;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Exponential;
            RenderSettings.fogColor = midday.fogColor;
            RenderSettings.fogDensity = midday.fogDensity;

            // Cámara real: la mueve el CinemachineBrain según la CinemachineCamera activa.
            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            camGo.AddComponent<Camera>();
            camGo.AddComponent<AudioListener>();
            camGo.AddComponent<UniversalAdditionalCameraData>().renderPostProcessing = true;
            camGo.AddComponent<CinemachineBrain>().DefaultBlend =
                new CinemachineBlendDefinition(CinemachineBlendDefinition.Styles.EaseInOut, 0.5f);

            var player = (GameObject)PrefabUtility.InstantiatePrefab(BuildPlayerPrefab());
            player.transform.SetPositionAndRotation(new Vector3(0f, 0f, -2f), Quaternion.identity);
            var rig = BuildCameraRig(player);
            var hud = BuildHud(player.GetComponent<PlayerInteractor>());
            var paintMode = BuildPaintMode(rig, player, hud);
            var placer = BuildPaintingPlacer(hud.transform, player, seasonClock);
            BuildInventoryUI(hud.transform, player.GetComponent<PlayerInventory>(), placer, paintMode,
                rig.GetComponent<CursorLock>(), rig.GetComponent<CameraModeController>(),
                paintMode.GetComponent<PaintBrushController>(), player.GetComponent<PigmentStock>());
            BuildCoinCounter(hud.transform, player.GetComponent<Wallet>());
            BuildLevelCounter(hud.transform, player.GetComponent<ArtistLevel>());
            BuildSeasonCounter(hud.transform, seasonClock);
            BuildTutorialObjectives(hud.transform, player, paintMode, placer);
            var calendarUi = BuildCalendarUI(hud.transform, player, rig, seasonClock, paintMode, placer);
            BuildWallCalendar(environment.transform, calendarUi, seasonClock);
            BuildTestLamp(environment.transform, new Vector3(-4.5f, 0.8f, 4.2f));
            BuildSellCrate(environment.transform, new Vector3(-4.6f, 0f, 1.5f));
            BuildShop(hud.transform, environment.transform, player, rig, seasonClock);
            BuildCropPicker(hud.transform, player, rig, seasonClock);
            BuildMortar(hud.transform, environment.transform, player, rig, paintMode.GetComponent<PaintBrushController>());
            BuildGarden(player.GetComponent<ArtistLevel>());
            BuildLantern(environment.transform, "Lantern_StudioFront", new Vector3(1.9f, 0f, -6.6f));
            BuildLantern(environment.transform, "Lantern_StudioInside", new Vector3(3.4f, 0f, 3.4f)); // luz cálida junto al caballete de noche
            var dialogueUi = BuildDialogueUI(hud.transform, player, rig);
            var commissionUi = BuildCommissionUI(hud.transform, player, rig);
            var gallery = BuildGallery(hud.transform, dialogueUi, commissionUi, player, rig, wallMat, paintMode.GetComponent<PaintBrushController>(), seasonClock);
            var town = BuildTown();
            BuildArtDealer(hud.transform, town, dialogueUi, player, rig, paintMode.GetComponent<PaintBrushController>(), seasonClock);
            BuildNoticeBoard(town, dialogueUi, commissionUi, player, paintMode.GetComponent<PaintBrushController>());
            BuildFestival(town, gallery, dialogueUi, commissionUi, player, paintMode.GetComponent<PaintBrushController>(), seasonClock);
            var saveManager = BuildSaveManager(player); // al final: ya existen todos los assets de datos
            BuildPauseMenu(hud.transform, player, rig, paintMode, placer, saveManager);
            BuildAudio(player, seasonClock);
            BuildFeedback();

            BuildDayFade(hud.transform, seasonClock); // el último hijo del HUD: cubre todo lo demás

            // Caballete delante del punto de inicio, mirando hacia el jugador.
            var easel = (GameObject)PrefabUtility.InstantiatePrefab(BuildEaselPrefab());
            easel.transform.SetPositionAndRotation(new Vector3(1.5f, 0f, 1.5f), Quaternion.Euler(0f, 200f, 0f));

            var volumeGo = new GameObject("Global Volume");
            var volume = volumeGo.AddComponent<Volume>();
            volume.isGlobal = true;
            volume.sharedProfile = CreateVolumeProfile();

            // Volúmenes locales por zona, sutiles y por encima del global.
            BuildZoneVolume("Volume_Studio", new Vector3(0f, 1.6f, 0f), new Vector3(12f, 3.2f, 12f), StudioZoneProfilePath, 6f, 4f);
            BuildZoneVolume("Volume_Gallery", new Vector3(0f, 1.6f, 10f), new Vector3(12f, 3.2f, 8f), GalleryZoneProfilePath, -4f, -6f);

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets();

            // DefaultControls registra cada paso (crear, emparentar) en el Undo del editor. En Play mode,
            // Ctrl+Z en la Game view también dispara ese Undo y desarmaba la UI. La escena es generada:
            // no hay nada que deshacer.
            Undo.ClearAll();
            Debug.Log($"[StudioSceneBuilder] Scene generated at {ScenePath}");
        }

        static bool HasOtherModifiedScenes()
        {
            for (int i = 0; i < UnityEngine.SceneManagement.SceneManager.sceneCount; i++)
            {
                var s = UnityEngine.SceneManagement.SceneManager.GetSceneAt(i);
                if (s.isDirty && s.path != ScenePath) return true;
            }
            return false;
        }

        /// <summary>Jugador placeholder: cápsula con visera para ver hacia dónde mira.</summary>
        static GameObject BuildPlayerPrefab()
        {
            var root = new GameObject("Player") { tag = "Player" };

            var controller = root.AddComponent<CharacterController>();
            controller.height = 1.8f;
            controller.radius = 0.35f;
            controller.center = new Vector3(0f, 0.9f, 0f);

            var movement = root.AddComponent<PlayerMovement>();
            var so = new SerializedObject(movement);
            so.FindProperty("moveAction").objectReferenceValue = GetAction("Player/Move");
            so.FindProperty("sprintAction").objectReferenceValue = GetAction("Player/Sprint");
            so.ApplyModifiedPropertiesWithoutUndo();

            var inventory = new SerializedObject(root.AddComponent<PlayerInventory>());
            inventory.FindProperty("startingCanvasType").objectReferenceValue = GetOrCreateCanvasTypes()[0];
            inventory.ApplyModifiedPropertiesWithoutUndo();
            root.AddComponent<Wallet>();
            root.AddComponent<ArtistLevel>();
            root.AddComponent<PigmentStock>().EditorSetStartingAmounts(
                GetOrCreatePalette().Take(StartingPigments).ToArray(), new[] { 150, 40, 50 });
            var sketchbook = new SerializedObject(root.AddComponent<Sketchbook>());
            SetArray(sketchbook.FindProperty("knownCrops"), GetOrCreateCrops().Take(StartingCrops).ToArray());
            sketchbook.ApplyModifiedPropertiesWithoutUndo();
            var interactor = new SerializedObject(root.AddComponent<PlayerInteractor>());
            interactor.FindProperty("interactAction").objectReferenceValue = GetAction("Player/Interact");
            interactor.ApplyModifiedPropertiesWithoutUndo();

            var visuals = new GameObject("Visuals");
            visuals.transform.SetParent(root.transform, false);

            var body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            body.name = "Body";
            Object.DestroyImmediate(body.GetComponent<Collider>());
            body.transform.SetParent(visuals.transform, false);
            body.transform.localPosition = new Vector3(0f, 0.9f, 0f);
            body.transform.localScale = new Vector3(0.7f, 0.9f, 0.7f);
            body.GetComponent<MeshRenderer>().sharedMaterial = GetOrCreateMaterial("M_Player_Body", new Color(0.36f, 0.52f, 0.62f));

            var visor = GameObject.CreatePrimitive(PrimitiveType.Cube);
            visor.name = "Visor";
            Object.DestroyImmediate(visor.GetComponent<Collider>());
            visor.transform.SetParent(visuals.transform, false);
            visor.transform.localPosition = new Vector3(0f, 1.5f, 0.3f);
            visor.transform.localScale = new Vector3(0.45f, 0.14f, 0.15f);
            visor.GetComponent<MeshRenderer>().sharedMaterial = GetOrCreateMaterial("M_Player_Visor", new Color(0.15f, 0.12f, 0.1f));

            new GameObject("EyePoint").transform.SetParent(root.transform, false);
            root.transform.Find("EyePoint").localPosition = new Vector3(0f, 1.6f, 0.1f);

            var prefab = PrefabUtility.SaveAsPrefabAsset(root, PlayerPrefabPath);
            Object.DestroyImmediate(root);
            return prefab;
        }

        static GameObject BuildCameraRig(GameObject player)
        {
            var rig = new GameObject("Cameras");
            rig.AddComponent<CursorLock>();

            // Primera persona: fija en los ojos, mirar con ratón/stick.
            var fpGo = new GameObject("CM FirstPerson");
            fpGo.transform.SetParent(rig.transform, false);
            var fp = fpGo.AddComponent<CinemachineCamera>();
            fp.Follow = player.transform.Find("EyePoint");
            fp.Priority = 10; // activa también en el editor; en juego la gestiona CameraModeController
            fp.Lens.FieldOfView = 65f;
            fp.Lens.NearClipPlane = 0.05f;
            fpGo.AddComponent<CinemachineHardLockToTarget>();
            fpGo.AddComponent<CinemachinePanTilt>().ReferenceFrame = CinemachinePanTilt.ReferenceFrames.World;
            AddLookInput(fpGo);

            // Vista fija: sin componentes de movimiento; CameraModeController la coloca (ej. frente al lienzo).
            var fixedGo = new GameObject("CM FixedView");
            fixedGo.transform.SetParent(rig.transform, false);
            var fixedCam = fixedGo.AddComponent<CinemachineCamera>();
            fixedCam.Lens.FieldOfView = 50f;
            fixedCam.Lens.NearClipPlane = 0.05f;

            var modeController = rig.AddComponent<CameraModeController>();
            var so = new SerializedObject(modeController);
            so.FindProperty("firstPersonCamera").objectReferenceValue = fp;
            so.FindProperty("fixedViewCamera").objectReferenceValue = fixedCam;
            so.FindProperty("playerMovement").objectReferenceValue = player.GetComponent<PlayerMovement>();
            so.FindProperty("playerVisuals").objectReferenceValue = player.transform.Find("Visuals").gameObject;
            so.ApplyModifiedPropertiesWithoutUndo();
            return rig;
        }

        static PaintModeController BuildPaintMode(GameObject rig, GameObject player, GameObject hud)
        {
            // Los clics en la UI necesitan un EventSystem con el módulo del Input System nuevo.
            var eventSystem = new GameObject("EventSystem", typeof(EventSystem));
            eventSystem.AddComponent<InputSystemUIInputModule>();

            var paintHud = new GameObject("PaintHUD", typeof(RectTransform));
            paintHud.transform.SetParent(hud.transform, false);
            var hudRect = (RectTransform)paintHud.transform;
            hudRect.anchorMin = Vector2.zero;
            hudRect.anchorMax = Vector2.one;
            hudRect.offsetMin = hudRect.offsetMax = Vector2.zero;

            var paintMode = new GameObject("PaintMode").AddComponent<PaintModeController>();
            var so = new SerializedObject(paintMode);
            so.FindProperty("cameraMode").objectReferenceValue = rig.GetComponent<CameraModeController>();
            so.FindProperty("interactor").objectReferenceValue = player.GetComponent<PlayerInteractor>();
            so.FindProperty("cursorLock").objectReferenceValue = rig.GetComponent<CursorLock>();
            so.FindProperty("exitAction").objectReferenceValue = GetAction("Paint/Exit");
            so.FindProperty("paintHud").objectReferenceValue = paintHud;
            so.ApplyModifiedPropertiesWithoutUndo();

            // Aro del cursor de pincel: imagen de UI (el sprite del aro se genera en runtime).
            var ringGo = new GameObject("BrushCursor", typeof(RectTransform), typeof(Image));
            ringGo.transform.SetParent(hud.transform, false);
            var ring = ringGo.GetComponent<Image>();
            ring.color = new Color(0.2f, 0.14f, 0.1f, 0.9f);
            ring.raycastTarget = false;

            var brush = paintMode.gameObject.AddComponent<PaintBrushController>();
            var brushSo = new SerializedObject(brush);
            brushSo.FindProperty("paintMode").objectReferenceValue = paintMode;
            brushSo.FindProperty("pointAction").objectReferenceValue = GetAction("Paint/Point");
            brushSo.FindProperty("strokeAction").objectReferenceValue = GetAction("Paint/Stroke");
            brushSo.FindProperty("brushSizeAction").objectReferenceValue = GetAction("Paint/BrushSize");
            brushSo.FindProperty("undoAction").objectReferenceValue = GetAction("Paint/Undo");
            brushSo.FindProperty("redoAction").objectReferenceValue = GetAction("Paint/Redo");
            brushSo.FindProperty("cursorRing").objectReferenceValue = ring;
            var paletteProp = brushSo.FindProperty("palette");
            // Solo los colores del girasol al empezar; el resto se compra en la tienda.
            var pigments = GetOrCreatePalette().Take(StartingPigments).ToArray();
            paletteProp.arraySize = pigments.Length;
            for (int i = 0; i < pigments.Length; i++)
                paletteProp.GetArrayElementAtIndex(i).objectReferenceValue = pigments[i];
            // Solo el pincel redondo al empezar; el resto se compra en la tienda.
            SetArray(brushSo.FindProperty("brushes"), GetOrCreateBrushes().Take(StartingBrushes).ToArray());
            brushSo.ApplyModifiedPropertiesWithoutUndo();

            BuildHeldBrush(brush);

            // El mensaje vive en el HUD raíz para que la enhorabuena siga visible al salir del modo pintura.
            var finisher = paintMode.gameObject.AddComponent<PaintingFinisher>();
            var finisherSo = new SerializedObject(finisher);
            finisherSo.FindProperty("paintMode").objectReferenceValue = paintMode;
            finisherSo.FindProperty("feedback").objectReferenceValue = BuildFeedback(hud.transform);
            finisherSo.FindProperty("brush").objectReferenceValue = brush;
            finisherSo.FindProperty("stock").objectReferenceValue = player.GetComponent<PigmentStock>();
            finisherSo.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
            finisherSo.ApplyModifiedPropertiesWithoutUndo();

            BuildPalettePanel(paintHud.transform, paintMode, brush, finisher, player.GetComponent<PigmentStock>());
            BuildCoverageReadout(paintHud.transform, paintMode, brush);
            return paintMode;
        }

        /// <summary>Pincel en mano de primera persona: mango, virola y punta (punta en el origen, mango hacia +Y); HeldBrush lo coloca en el lienzo.</summary>
        static void BuildHeldBrush(PaintBrushController brush)
        {
            var root = new GameObject("HeldBrush");
            var visual = new GameObject("Visual").transform;
            visual.SetParent(root.transform, false);
            var tipMat = GetOrCreateMaterial("M_HeldBrush_Tip", Color.white); // el color real va por MaterialPropertyBlock
            var ferruleMat = GetOrCreateMaterial("M_HeldBrush_Ferrule", new Color(0.62f, 0.62f, 0.66f));
            var handleMat = GetOrCreateMaterial("M_HeldBrush_Handle", new Color(0.55f, 0.36f, 0.20f));
            var tip = CreatePart(PrimitiveType.Sphere, "Tip", visual, new Vector3(0f, 0.02f, 0f), new Vector3(0.016f, 0.04f, 0.016f), tipMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cylinder, "Ferrule", visual, new Vector3(0f, 0.065f, 0f), new Vector3(0.014f, 0.025f, 0.014f), ferruleMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cylinder, "Handle", visual, new Vector3(0f, 0.2f, 0f), new Vector3(0.011f, 0.11f, 0.011f), handleMat, Quaternion.identity);
            foreach (var r in visual.GetComponentsInChildren<MeshRenderer>())
            {
                r.shadowCastingMode = ShadowCastingMode.Off;
                r.receiveShadows = false;
            }

            var held = root.AddComponent<HeldBrush>();
            var so = new SerializedObject(held);
            so.FindProperty("brush").objectReferenceValue = brush;
            so.FindProperty("visual").objectReferenceValue = visual.gameObject;
            so.FindProperty("tip").objectReferenceValue = tip.GetComponent<MeshRenderer>();
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Colocar pinturas del inventario en el suelo: controlador, aviso y prefab de la parcela.</summary>
        static PaintingPlacer BuildPaintingPlacer(Transform hud, GameObject player, SeasonClock seasonClock)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var hint = CreatePanel(hud, "PlacementHint", AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd"),
                new Color(0.16f, 0.11f, 0.08f, 0.85f), new Vector2(0.5f, 0f), new Vector2(0f, 120f), new Vector2(620f, 60f));
            var label = AddStretchedText(hint.transform, "Label", 24, font, new Color(1f, 0.95f, 0.82f), TextAnchor.MiddleCenter);
            hint.SetActive(false);

            var placer = new GameObject("PaintingPlacer").AddComponent<PaintingPlacer>();
            var so = new SerializedObject(placer);
            so.FindProperty("inventory").objectReferenceValue = player.GetComponent<PlayerInventory>();
            so.FindProperty("interactor").objectReferenceValue = player.GetComponent<PlayerInteractor>();
            so.FindProperty("plotPrefab").objectReferenceValue = BuildPaintingPlotPrefab();
            so.FindProperty("seasons").objectReferenceValue = seasonClock;
            so.FindProperty("confirmAction").objectReferenceValue = GetAction("Player/Interact");
            so.FindProperty("cancelAction").objectReferenceValue = GetAction("Paint/Exit");
            so.FindProperty("hint").objectReferenceValue = hint;
            so.FindProperty("hintLabel").objectReferenceValue = label;
            so.ApplyModifiedPropertiesWithoutUndo();
            return placer;
        }

        /// <summary>
        /// Parcela: el lienzo con su marco, plano en el suelo y con la pintura hacia arriba.
        /// La parte de arriba de la pintura apunta hacia delante (+Z): se lee derecha desde quien la colocó.
        /// </summary>
        static PaintingPlot BuildPaintingPlotPrefab()
        {
            var root = new GameObject("PaintingPlot");
            var box = root.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, 0.02f, 0f);
            box.size = new Vector3(1.06f, 0.04f, 0.86f);

            CreatePart(PrimitiveType.Cube, "Frame", root.transform, new Vector3(0f, 0.015f, 0f), new Vector3(1.06f, 0.03f, 0.86f),
                GetOrCreateMaterial("M_Easel_Wood", new Color(0.42f, 0.28f, 0.18f)), Quaternion.identity);
            var painting = CreatePart(PrimitiveType.Quad, "Painting", root.transform, new Vector3(0f, 0.032f, 0f), new Vector3(1f, 0.8f, 1f),
                GetOrCreateMaterial("M_PaintingPlot", Color.white), Quaternion.Euler(90f, 0f, 0f));
            Object.DestroyImmediate(painting.GetComponent<Collider>()); // basta con el BoxCollider de la raíz

            var plot = root.AddComponent<PaintingPlot>();
            var so = new SerializedObject(plot);
            so.FindProperty("paintingRenderer").objectReferenceValue = painting.GetComponent<MeshRenderer>();
            var colliders = so.FindProperty("colliders");
            colliders.arraySize = 1;
            colliders.GetArrayElementAtIndex(0).objectReferenceValue = box;
            so.ApplyModifiedPropertiesWithoutUndo();

            var prefab = PrefabUtility.SaveAsPrefabAsset(root, PaintingPlotPrefabPath);
            Object.DestroyImmediate(root);
            return prefab.GetComponent<PaintingPlot>();
        }

        /// <summary>
        /// Inventario placeholder: aviso "+1 ..." arriba al centro y panel con casillas (I / Tab / Y).
        /// </summary>
        static void BuildInventoryUI(Transform hud, PlayerInventory inventory, PaintingPlacer placer,
            PaintModeController paintMode, CursorLock cursorLock, CameraModeController cameraMode,
            PaintBrushController brush, PigmentStock stock)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var cream = new Color(1f, 0.95f, 0.82f);
            var uiSprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");

            var root = new GameObject("InventoryUI", typeof(RectTransform));
            root.transform.SetParent(hud, false);
            var rootRect = (RectTransform)root.transform;
            rootRect.anchorMin = Vector2.zero;
            rootRect.anchorMax = Vector2.one;
            rootRect.offsetMin = rootRect.offsetMax = Vector2.zero;

            // Aviso al recoger algo.
            var toast = CreatePanel(root.transform, "Toast", uiSprite, new Color(0.22f, 0.36f, 0.16f, 0.92f),
                new Vector2(0.5f, 1f), new Vector2(0f, -40f), new Vector2(560f, 100f));
            var toastLabel = AddStretchedText(toast.transform, "Label", 26, font, cream, TextAnchor.MiddleCenter);

            // Panel del inventario.
            var panel = CreatePanel(root.transform, "Panel", uiSprite, new Color(0.30f, 0.20f, 0.13f, 0.95f),
                new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(760f, 580f));
            var title = AddStretchedText(panel.transform, "Title", 32, font, cream, TextAnchor.UpperCenter);
            title.text = "Inventory";

            // Fila de pigmentos bajo el título: una ficha (color + cantidad) por color de la paleta.
            var pigments = new GameObject("Pigments", typeof(RectTransform), typeof(HorizontalLayoutGroup));
            pigments.transform.SetParent(panel.transform, false);
            var pigmentsRect = (RectTransform)pigments.transform;
            pigmentsRect.anchorMin = new Vector2(0f, 1f);
            pigmentsRect.anchorMax = Vector2.one;
            pigmentsRect.pivot = new Vector2(0.5f, 1f);
            pigmentsRect.anchoredPosition = new Vector2(0f, -64f);
            pigmentsRect.sizeDelta = new Vector2(-60f, 44f);
            var pigmentsLayout = pigments.GetComponent<HorizontalLayoutGroup>();
            pigmentsLayout.spacing = 14f;
            pigmentsLayout.childAlignment = TextAnchor.MiddleCenter;
            pigmentsLayout.childControlWidth = pigmentsLayout.childControlHeight = true;
            pigmentsLayout.childForceExpandWidth = pigmentsLayout.childForceExpandHeight = false;

            var chip = new GameObject("PigmentTemplate", typeof(RectTransform), typeof(LayoutElement));
            chip.transform.SetParent(pigments.transform, false);
            var chipLayout = chip.GetComponent<LayoutElement>();
            chipLayout.preferredWidth = 96f;
            chipLayout.preferredHeight = 40f;
            var swatch = new GameObject("Swatch", typeof(RectTransform), typeof(Image));
            swatch.transform.SetParent(chip.transform, false);
            var swatchRect = (RectTransform)swatch.transform;
            swatchRect.anchorMin = swatchRect.anchorMax = swatchRect.pivot = new Vector2(0f, 0.5f);
            swatchRect.sizeDelta = new Vector2(36f, 36f);
            var swatchImage = swatch.GetComponent<Image>();
            swatchImage.sprite = uiSprite;
            swatchImage.type = Image.Type.Sliced;
            swatchImage.raycastTarget = false;
            var amount = AddStretchedText(chip.transform, "Amount", 22, font, cream, TextAnchor.MiddleLeft);
            ((RectTransform)amount.transform).offsetMin = new Vector2(44f, 0f);
            ((RectTransform)title.transform).offsetMax = new Vector2(0f, -16f);

            var hint = AddStretchedText(panel.transform, "Hint", 18, font, cream, TextAnchor.LowerCenter);
            hint.text = "Click a painting to place it on the floor   ·   [I] or [Tab] to close";
            ((RectTransform)hint.transform).offsetMin = new Vector2(0f, 12f);

            var empty = AddStretchedText(panel.transform, "Empty", 22, font, cream, TextAnchor.MiddleCenter);
            empty.text = "Nothing here yet. Finish a painting and take it from the easel.";

            var grid = new GameObject("Slots", typeof(RectTransform), typeof(GridLayoutGroup));
            grid.transform.SetParent(panel.transform, false);
            var gridRect = (RectTransform)grid.transform;
            gridRect.anchorMin = Vector2.zero;
            gridRect.anchorMax = Vector2.one;
            gridRect.offsetMin = new Vector2(30f, 50f);
            gridRect.offsetMax = new Vector2(-30f, -120f);
            var layout = grid.GetComponent<GridLayoutGroup>();
            layout.cellSize = new Vector2(160f, 180f);
            layout.spacing = new Vector2(16f, 16f);
            layout.childAlignment = TextAnchor.UpperLeft;

            // Casilla plantilla: miniatura 5:4 (como el lienzo) + nombre y calidad.
            var slot = new GameObject("SlotTemplate", typeof(RectTransform), typeof(Image), typeof(Button));
            slot.transform.SetParent(grid.transform, false);
            var slotImage = slot.GetComponent<Image>();
            slotImage.sprite = uiSprite;
            slotImage.type = Image.Type.Sliced;
            slotImage.color = new Color(0.93f, 0.88f, 0.78f);
            slot.GetComponent<Button>().targetGraphic = slotImage;

            var icon = new GameObject("Icon", typeof(RectTransform), typeof(RawImage));
            icon.transform.SetParent(slot.transform, false);
            var iconRect = (RectTransform)icon.transform;
            iconRect.anchorMin = iconRect.anchorMax = iconRect.pivot = new Vector2(0.5f, 1f);
            iconRect.anchoredPosition = new Vector2(0f, -8f);
            iconRect.sizeDelta = new Vector2(144f, 115f);

            var nameText = AddStretchedText(slot.transform, "Name", 17, font, new Color(0.25f, 0.17f, 0.1f), TextAnchor.LowerCenter);
            ((RectTransform)nameText.transform).offsetMin = new Vector2(4f, 6f);

            var ui = root.AddComponent<InventoryUI>();
            var so = new SerializedObject(ui);
            so.FindProperty("inventory").objectReferenceValue = inventory;
            so.FindProperty("toggleAction").objectReferenceValue = GetAction("Player/Inventory");
            so.FindProperty("placer").objectReferenceValue = placer;
            so.FindProperty("paintMode").objectReferenceValue = paintMode;
            so.FindProperty("cursorLock").objectReferenceValue = cursorLock;
            so.FindProperty("cameraMode").objectReferenceValue = cameraMode;
            so.FindProperty("panel").objectReferenceValue = panel;
            so.FindProperty("slotContainer").objectReferenceValue = gridRect;
            so.FindProperty("slotTemplate").objectReferenceValue = slot.GetComponent<Button>();
            so.FindProperty("emptyLabel").objectReferenceValue = empty.gameObject;
            so.FindProperty("brush").objectReferenceValue = brush;
            so.FindProperty("stock").objectReferenceValue = stock;
            so.FindProperty("pigmentContainer").objectReferenceValue = pigmentsRect;
            so.FindProperty("pigmentTemplate").objectReferenceValue = chip;
            so.FindProperty("toast").objectReferenceValue = toast;
            so.FindProperty("toastLabel").objectReferenceValue = toastLabel;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static GameObject CreatePanel(Transform parent, string name, Sprite sprite, Color color, Vector2 anchor, Vector2 position, Vector2 size)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            var rect = (RectTransform)go.transform;
            rect.anchorMin = rect.anchorMax = rect.pivot = anchor;
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
            var image = go.GetComponent<Image>();
            image.sprite = sprite;
            image.type = Image.Type.Sliced;
            image.color = color;
            image.raycastTarget = false;
            return go;
        }

        static Text AddStretchedText(Transform parent, string name, int fontSize, Font font, Color color, TextAnchor alignment)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Text));
            go.transform.SetParent(parent, false);
            var rect = (RectTransform)go.transform;
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.offsetMin = rect.offsetMax = Vector2.zero;
            var text = go.GetComponent<Text>();
            text.font = font;
            text.fontSize = fontSize;
            text.color = color;
            text.alignment = alignment;
            text.raycastTarget = false;
            return text;
        }

        /// <summary>Mensaje temporal abajo al centro, por encima del aviso de interacción.</summary>
        static PaintFeedbackUI BuildFeedback(Transform hud)
        {
            var root = new GameObject("PaintFeedback", typeof(RectTransform), typeof(PaintFeedbackUI));
            root.transform.SetParent(hud, false);
            var rootRect = (RectTransform)root.transform;
            rootRect.anchorMin = Vector2.zero;
            rootRect.anchorMax = Vector2.one;
            rootRect.offsetMin = rootRect.offsetMax = Vector2.zero;

            var panel = new GameObject("Panel", typeof(RectTransform), typeof(Image), typeof(VerticalLayoutGroup), typeof(ContentSizeFitter));
            panel.transform.SetParent(root.transform, false);
            var rect = (RectTransform)panel.transform;
            rect.anchorMin = rect.anchorMax = rect.pivot = new Vector2(0.5f, 0f);
            rect.anchoredPosition = new Vector2(0f, 60f);
            rect.sizeDelta = new Vector2(760f, 0f);
            var image = panel.GetComponent<Image>();
            image.sprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");
            image.type = Image.Type.Sliced;
            image.raycastTarget = false;
            var layout = panel.GetComponent<VerticalLayoutGroup>();
            layout.padding = new RectOffset(24, 24, 16, 16);
            layout.childControlWidth = layout.childControlHeight = true;
            layout.childForceExpandHeight = false;
            panel.GetComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            var labelGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
            labelGo.transform.SetParent(panel.transform, false);
            var label = labelGo.GetComponent<Text>();
            label.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            label.fontSize = 28;
            label.alignment = TextAnchor.MiddleCenter;
            label.color = new Color(1f, 0.95f, 0.82f);
            label.raycastTarget = false;

            var feedback = root.GetComponent<PaintFeedbackUI>();
            var so = new SerializedObject(feedback);
            so.FindProperty("panel").objectReferenceValue = panel;
            so.FindProperty("background").objectReferenceValue = image;
            so.FindProperty("label").objectReferenceValue = label;
            so.ApplyModifiedPropertiesWithoutUndo();
            return feedback;
        }

        /// <summary>Lectura de depuración de cobertura, arriba a la derecha (Fase 3C).</summary>
        static void BuildCoverageReadout(Transform parent, PaintModeController paintMode, PaintBrushController brush)
        {
            // El alto se ajusta al texto (VerticalLayoutGroup + ContentSizeFitter).
            var panel = new GameObject("CoverageReadout", typeof(RectTransform), typeof(Image), typeof(VerticalLayoutGroup), typeof(ContentSizeFitter));
            panel.transform.SetParent(parent, false);
            var rect = (RectTransform)panel.transform;
            rect.anchorMin = rect.anchorMax = rect.pivot = new Vector2(1f, 1f);
            rect.anchoredPosition = new Vector2(-30f, -265f); // bajo monedas, nivel y estación
            rect.sizeDelta = new Vector2(320f, 0f);
            var layout = panel.GetComponent<VerticalLayoutGroup>();
            layout.padding = new RectOffset(16, 16, 12, 12);
            layout.childControlWidth = layout.childControlHeight = true;
            layout.childForceExpandWidth = true;
            layout.childForceExpandHeight = false;
            panel.GetComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;
            var image = panel.GetComponent<Image>();
            image.sprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");
            image.type = Image.Type.Sliced;
            image.color = new Color(0.12f, 0.09f, 0.07f, 0.8f);
            image.raycastTarget = false;

            var labelGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
            labelGo.transform.SetParent(panel.transform, false);
            var label = labelGo.GetComponent<Text>();
            label.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            label.fontSize = 22;
            label.alignment = TextAnchor.UpperLeft;
            label.color = new Color(1f, 0.95f, 0.82f);
            label.raycastTarget = false;

            var readout = panel.AddComponent<CoverageReadoutUI>();
            var so = new SerializedObject(readout);
            so.FindProperty("paintMode").objectReferenceValue = paintMode;
            so.FindProperty("brush").objectReferenceValue = brush;
            so.FindProperty("label").objectReferenceValue = label;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Paleta lateral de madera: muestras de color, tamaño, borrador y cómo salir.</summary>
        static void BuildPalettePanel(Transform parent, PaintModeController paintMode, PaintBrushController brush, PaintingFinisher finisher, PigmentStock stock)
        {
            var resources = new DefaultControls.Resources
            {
                standard = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd"),
                background = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Background.psd"),
                knob = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Knob.psd")
            };
            var cream = new Color(1f, 0.95f, 0.82f);
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

            var panel = new GameObject("PalettePanel", typeof(RectTransform), typeof(Image), typeof(VerticalLayoutGroup));
            panel.transform.SetParent(parent, false);
            var panelRect = (RectTransform)panel.transform;
            panelRect.anchorMin = panelRect.anchorMax = new Vector2(0f, 0.5f);
            panelRect.pivot = new Vector2(0f, 0.5f);
            panelRect.anchoredPosition = new Vector2(40f, 0f);
            panelRect.sizeDelta = new Vector2(300f, 1022f); // ancho para 4 botones en la fila de herramientas; alto: ver suma de la columna (1002)
            panel.AddComponent<FitToScreenHeight>(); // con la interfaz agrandada no se sale por arriba ni por abajo
            var panelImage = panel.GetComponent<Image>();
            panelImage.sprite = resources.standard;
            panelImage.type = Image.Type.Sliced;
            panelImage.color = new Color(0.45f, 0.30f, 0.19f, 0.95f);
            var layout = panel.GetComponent<VerticalLayoutGroup>();
            layout.padding = new RectOffset(18, 18, 18, 18);
            layout.spacing = 14f;
            layout.childAlignment = TextAnchor.UpperCenter;
            layout.childControlWidth = true;
            layout.childControlHeight = true;
            layout.childForceExpandWidth = true;
            layout.childForceExpandHeight = false;

            AddLabel(panel.transform, "Title", "Palette", 30, 40f, font, cream);
            var currentColor = AddLabel(panel.transform, "CurrentColor", "Color", 22, 28f, font, cream);

            // Muestras: PaintToolsUI clona la plantilla por cada pigmento de la paleta.
            var swatches = new GameObject("Swatches", typeof(RectTransform), typeof(GridLayoutGroup), typeof(LayoutElement));
            swatches.transform.SetParent(panel.transform, false);
            var grid = swatches.GetComponent<GridLayoutGroup>();
            grid.cellSize = new Vector2(90f, 90f);
            grid.spacing = new Vector2(14f, 14f);
            grid.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
            grid.constraintCount = 2;
            grid.childAlignment = TextAnchor.UpperCenter;
            swatches.GetComponent<LayoutElement>().preferredHeight = 3 * 90f + 2 * 14f;

            var template = new GameObject("SwatchTemplate", typeof(RectTransform), typeof(Image), typeof(Button), typeof(Outline));
            template.transform.SetParent(swatches.transform, false);
            var templateImage = template.GetComponent<Image>();
            templateImage.sprite = resources.standard;
            templateImage.type = Image.Type.Sliced;
            template.GetComponent<Button>().targetGraphic = templateImage;
            ConfigureHighlight(template.GetComponent<Outline>(), cream);
            var amount = AddStretchedText(template.transform, "Amount", 20, font, Color.white, TextAnchor.UpperRight);
            ((RectTransform)amount.transform).offsetMax = new Vector2(-6f, -4f);
            ((RectTransform)amount.transform).offsetMin = new Vector2(0f, 30f); // deja libre la franja del nombre
            var amountShadow = amount.gameObject.AddComponent<Shadow>(); // legible sobre el blanco y el amarillo
            amountShadow.effectColor = new Color(0f, 0f, 0f, 0.8f);
            amountShadow.effectDistance = new Vector2(1.5f, -1.5f);

            // Nombre del pigmento sobre una franja oscura: legible con cualquier color de muestra.
            var nameStrip = CreatePanel(template.transform, "NameStrip", resources.standard, new Color(0.1f, 0.07f, 0.05f, 0.65f),
                new Vector2(0.5f, 0f), Vector2.zero, new Vector2(0f, 30f));
            var stripRect = (RectTransform)nameStrip.transform;
            stripRect.anchorMin = Vector2.zero;
            stripRect.anchorMax = new Vector2(1f, 0f);
            stripRect.offsetMin = Vector2.zero;
            stripRect.offsetMax = new Vector2(0f, 30f);
            var swatchName = AddStretchedText(nameStrip.transform, "Name", 16, font, Color.white, TextAnchor.MiddleCenter);
            swatchName.resizeTextForBestFit = true;
            swatchName.resizeTextMinSize = 10;
            swatchName.resizeTextMaxSize = 16;
            ((RectTransform)swatchName.transform).offsetMin = new Vector2(3f, 0f);
            ((RectTransform)swatchName.transform).offsetMax = new Vector2(-3f, 0f);

            AddLabel(panel.transform, "SizeLabel", "Brush size", 24, 30f, font, cream);
            var slider = DefaultControls.CreateSlider(resources);
            slider.name = "SizeSlider";
            slider.transform.SetParent(panel.transform, false);
            slider.AddComponent<LayoutElement>().preferredHeight = 30f;

            // Fila de herramientas: un botón por pincel (PaintToolsUI los clona delante) y el borrador.
            var toolsRow = CreateRow(panel.transform, "ToolsRow");
            var brushTemplate = CreateButton(resources, toolsRow, "BrushTemplate", "Brush", 18, font);
            ConfigureHighlight(brushTemplate.AddComponent<Outline>(), cream);
            var eraser = CreateButton(resources, toolsRow, "EraserButton", "Eraser", 18, font);
            ConfigureHighlight(eraser.AddComponent<Outline>(), cream);
            // Con 4 botones (~43 px cada uno) el texto se encoge para caber.
            foreach (var label in new[] { brushTemplate.GetComponentInChildren<Text>(), eraser.GetComponentInChildren<Text>() })
            {
                label.resizeTextForBestFit = true;
                label.resizeTextMinSize = 11;
                label.resizeTextMaxSize = 18;
            }

            // Herramientas compradas: PaintToolsUI activa cada botón al tenerla; la muestra, al copiar un color.
            var toolsRow2 = CreateRow(panel.transform, "ToolsRow2");
            var eyedropper = CreateButton(resources, toolsRow2, "EyedropperButton", "Eyedropper", 18, font);
            var symmetry = CreateButton(resources, toolsRow2, "SymmetryButton", "Symmetry", 18, font);
            var picked = CreateButton(resources, toolsRow2, "PickedButton", "Picked", 18, font);
            foreach (var toolButton in new[] { eyedropper, symmetry, picked })
            {
                ConfigureHighlight(toolButton.AddComponent<Outline>(), cream);
                var label = toolButton.GetComponentInChildren<Text>();
                label.resizeTextForBestFit = true;
                label.resizeTextMinSize = 11;
                label.resizeTextMaxSize = 18;
                toolButton.SetActive(false);
            }
            var pickedLabel = picked.GetComponentInChildren<Text>();
            pickedLabel.color = Color.white; // se lee sobre cualquier color copiado
            var pickedShadow = pickedLabel.gameObject.AddComponent<Shadow>();
            pickedShadow.effectColor = new Color(0f, 0f, 0f, 0.8f);
            pickedShadow.effectDistance = new Vector2(1.5f, -1.5f);

            var historyRow = CreateRow(panel.transform, "HistoryRow");
            var undo = CreateButton(resources, historyRow, "UndoButton", "Undo", 19, font);
            var redo = CreateButton(resources, historyRow, "RedoButton", "Redo", 19, font);
            var clear = CreateButton(resources, panel.transform, "ClearButton", "Clear canvas", 22, font);

            var guideRow = CreateRow(panel.transform, "GuideRow");
            var guide = CreateButton(resources, guideRow, "GuideButton", "Guide", 19, font);
            ConfigureHighlight(guide.AddComponent<Outline>(), cream);
            var hints = CreateButton(resources, guideRow, "HintsButton", "Color hints", 17, font);
            ConfigureHighlight(hints.AddComponent<Outline>(), cream);

            var finish = CreateButton(resources, panel.transform, "FinishButton", "Finish painting", 24, font);
            finish.GetComponent<Image>().color = new Color(0.98f, 0.80f, 0.32f);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(finish.GetComponent<Button>().onClick, finisher.Finish);

            AddLabel(panel.transform, "ExitHint", "Ctrl+Z undo  ·  Ctrl+Y redo\n[Esc] or [E] to exit", 17, 50f, font, cream);

            // Leyenda de zonas: a la derecha de la paleta, arriba; PaintToolsUI la rellena con la plantilla.
            var legend = CreatePanel(panel.transform, "ZoneLegend", resources.standard, new Color(0.12f, 0.09f, 0.07f, 0.8f),
                new Vector2(1f, 1f), new Vector2(20f, 0f), new Vector2(640f, 64f));
            legend.AddComponent<LayoutElement>().ignoreLayout = true;
            ((RectTransform)legend.transform).pivot = new Vector2(0f, 1f);
            var legendText = AddStretchedText(legend.transform, "Label", 22, font, cream, TextAnchor.MiddleLeft);
            legendText.resizeTextForBestFit = true;
            legendText.resizeTextMinSize = 14;
            legendText.resizeTextMaxSize = 22;
            ((RectTransform)legendText.transform).offsetMin = new Vector2(12f, 4f);
            ((RectTransform)legendText.transform).offsetMax = new Vector2(-12f, -4f);

            var tools = panel.AddComponent<PaintToolsUI>();
            var so = new SerializedObject(tools);
            so.FindProperty("brush").objectReferenceValue = brush;
            so.FindProperty("stock").objectReferenceValue = stock;
            so.FindProperty("paintMode").objectReferenceValue = paintMode;
            so.FindProperty("currentColorLabel").objectReferenceValue = currentColor;
            so.FindProperty("zoneLegendRoot").objectReferenceValue = legend;
            so.FindProperty("zoneLegendLabel").objectReferenceValue = legendText;
            so.FindProperty("swatchContainer").objectReferenceValue = swatches.transform;
            so.FindProperty("swatchTemplate").objectReferenceValue = template.GetComponent<Button>();
            so.FindProperty("sizeSlider").objectReferenceValue = slider.GetComponent<Slider>();
            so.FindProperty("brushTemplate").objectReferenceValue = brushTemplate.GetComponent<Button>();
            so.FindProperty("eraserButton").objectReferenceValue = eraser.GetComponent<Button>();
            so.FindProperty("eyedropperButton").objectReferenceValue = eyedropper.GetComponent<Button>();
            so.FindProperty("symmetryButton").objectReferenceValue = symmetry.GetComponent<Button>();
            so.FindProperty("pickedButton").objectReferenceValue = picked.GetComponent<Button>();
            so.FindProperty("undoButton").objectReferenceValue = undo.GetComponent<Button>();
            so.FindProperty("redoButton").objectReferenceValue = redo.GetComponent<Button>();
            so.FindProperty("clearButton").objectReferenceValue = clear.GetComponent<Button>();
            so.FindProperty("guideButton").objectReferenceValue = guide.GetComponent<Button>();
            so.FindProperty("hintsButton").objectReferenceValue = hints.GetComponent<Button>();
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static Transform CreateRow(Transform parent, string name)
        {
            var row = new GameObject(name, typeof(RectTransform), typeof(HorizontalLayoutGroup), typeof(LayoutElement));
            row.transform.SetParent(parent, false);
            row.GetComponent<LayoutElement>().preferredHeight = 56f;
            var layout = row.GetComponent<HorizontalLayoutGroup>();
            layout.spacing = 10f;
            layout.childControlWidth = layout.childControlHeight = true;
            layout.childForceExpandWidth = layout.childForceExpandHeight = true;
            return row.transform;
        }

        static GameObject CreateButton(DefaultControls.Resources resources, Transform parent, string name, string label, int fontSize, Font font)
        {
            var button = DefaultControls.CreateButton(resources);
            button.name = name;
            button.transform.SetParent(parent, false);
            button.AddComponent<LayoutElement>().preferredHeight = 56f;
            button.GetComponent<Image>().color = new Color(0.93f, 0.88f, 0.78f);
            var text = button.GetComponentInChildren<Text>();
            text.text = label;
            text.font = font;
            text.fontSize = fontSize;
            text.color = new Color(0.25f, 0.17f, 0.1f);
            return button;
        }

        static Text AddLabel(Transform parent, string name, string content, int fontSize, float height, Font font, Color color)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Text), typeof(LayoutElement));
            go.transform.SetParent(parent, false);
            go.GetComponent<LayoutElement>().preferredHeight = height;
            var text = go.GetComponent<Text>();
            text.text = content;
            text.font = font;
            text.fontSize = fontSize;
            text.alignment = TextAnchor.MiddleCenter;
            text.color = color;
            text.raycastTarget = false;
            return text;
        }

        /// <summary>Borde claro alrededor de la herramienta seleccionada (PaintToolsUI lo activa).</summary>
        static void ConfigureHighlight(Outline outline, Color color)
        {
            outline.effectColor = color;
            outline.effectDistance = new Vector2(4f, -4f);
            outline.enabled = false;
        }

        /// <summary>Los 6 pigmentos del vertical slice, en el orden de la paleta.</summary>
        /// <summary>Los primeros pinceles se tienen desde el principio.</summary>
        const int StartingBrushes = 1;

        static BrushDefinition[] GetOrCreateBrushes() => new[]
        {
            GetOrCreateBrush("round", "Round", BrushKind.Round),
            GetOrCreateBrush("fill", "Fill", BrushKind.Fill),
            GetOrCreateBrush("glaze", "Glaze", BrushKind.Glaze),
        };

        static BrushDefinition GetOrCreateBrush(string id, string displayName, BrushKind kind)
        {
            var path = $"{Root}/Data/Brushes/Brush_{id}.asset";
            var brush = AssetDatabase.LoadAssetAtPath<BrushDefinition>(path);
            if (brush == null)
            {
                brush = ScriptableObject.CreateInstance<BrushDefinition>();
                AssetDatabase.CreateAsset(brush, path);
            }
            brush.EditorSetup(id, displayName, kind);
            EditorUtility.SetDirty(brush);
            return brush;
        }

        /// <summary>Los estilos de pintura (assets en Data/Styles); ninguno se tiene al empezar, se compran en la tienda.</summary>
        static StyleDefinition[] GetOrCreateStyles()
        {
            if (!AssetDatabase.IsValidFolder($"{Root}/Data/Styles"))
                AssetDatabase.CreateFolder($"{Root}/Data", "Styles");

            var path = $"{Root}/Data/Styles/Style_wash.asset";
            var wash = AssetDatabase.LoadAssetAtPath<StyleDefinition>(path);
            if (wash == null)
            {
                wash = ScriptableObject.CreateInstance<StyleDefinition>();
                AssetDatabase.CreateAsset(wash, path);
            }
            wash.EditorSetup("wash", "Wash", "Soft see-through strokes. Half the pigment, forgiving spills, fast pastel crops.",
                StyleKind.Wash, newPigment: 0.5f, newSpill: 0.5f, newGrowth: 0.6f, newPastel: 0.25f, newSell: 1.25f);
            EditorUtility.SetDirty(wash);

            path = $"{Root}/Data/Styles/Style_swirl.asset";
            var swirl = AssetDatabase.LoadAssetAtPath<StyleDefinition>(path);
            if (swirl == null)
            {
                swirl = ScriptableObject.CreateInstance<StyleDefinition>();
                AssetDatabase.CreateAsset(swirl, path);
            }
            swirl.EditorSetup("swirl", "Swirl", "Swirling strokes reward long, flowing lines. Rare variants come easier.",
                StyleKind.Swirl, newPigment: 1f, newSpill: 1f, newGrowth: 1f, newPastel: 0f, newSell: 1.25f);
            EditorUtility.SetDirty(swirl);
            return new[] { wash, swirl };
        }

        /// <summary>Los primeros pigmentos de la paleta se tienen desde el principio.</summary>
        const int StartingPigments = 3;

        static PigmentDefinition[] GetOrCreatePalette() => new[]
        {
            GetOrCreatePigment("sunflower_yellow", "Sunflower Yellow", new Color(0.98f, 0.78f, 0.15f)),
            GetOrCreatePigment("burnt_ochre", "Burnt Ochre", new Color(0.55f, 0.33f, 0.13f)),
            GetOrCreatePigment("leaf_green", "Leaf Green", new Color(0.30f, 0.55f, 0.22f)),
            GetOrCreatePigment("ultramarine", "Ultramarine Blue", new Color(0.17f, 0.27f, 0.62f)),
            GetOrCreatePigment("carmine", "Carmine Red", new Color(0.75f, 0.15f, 0.17f)),
            GetOrCreatePigment("titanium_white", "Titanium White", new Color(0.98f, 0.98f, 0.96f)),
        };

        /// <summary>Los primeros cultivos se saben pintar desde el principio; el resto se compra (boceto).</summary>
        const int StartingCrops = 1;

        /// <summary>Híbridos al final de GetOrCreateCrops: se aprenden por polinización cruzada, no se venden.</summary>
        const int HybridCrops = 1;

        static CropDefinition[] GetOrCreateCrops()
        {
            var sunflower = GetOrCreateSunflowerCrop();
            var tomato = GetOrCreateTomatoCrop();
            var glowbell = GetOrCreateGlowbellCrop();
            var sunbell = GetOrCreateSunbellCrop();
            sunflower.EditorSetCrosses(new[] { new CropCross { partner = glowbell, hybrid = sunbell } });
            glowbell.EditorSetCrosses(new[] { new CropCross { partner = sunflower, hybrid = sunbell } });
            EditorUtility.SetDirty(sunflower);
            EditorUtility.SetDirty(glowbell);
            return new[] { sunflower, tomato, glowbell, sunbell };
        }

        static CropDefinition GetOrCreateCropAsset(string fileName)
        {
            var path = $"{Root}/Data/Crops/{fileName}.asset";
            var crop = AssetDatabase.LoadAssetAtPath<CropDefinition>(path);
            if (crop == null)
            {
                crop = ScriptableObject.CreateInstance<CropDefinition>();
                AssetDatabase.CreateAsset(crop, path);
            }
            return crop;
        }

        static PaintTemplate GetOrCreateTemplateAsset(string fileName)
        {
            var path = $"{Root}/Data/Templates/{fileName}.asset";
            var template = AssetDatabase.LoadAssetAtPath<PaintTemplate>(path);
            if (template == null)
            {
                template = ScriptableObject.CreateInstance<PaintTemplate>();
                AssetDatabase.CreateAsset(template, path);
            }
            return template;
        }

        /// <summary>Plantilla y cultivo del tomate. Los tomates sugieren el rojo, que se compra en la tienda.</summary>
        static CropDefinition GetOrCreateTomatoCrop()
        {
            var palette = GetOrCreatePalette();
            var mask = PaintTemplateGenerator.GenerateTomatoMask($"{Root}/Art/Textures/PaintTemplates/Tomato_Zones.png");

            var template = GetOrCreateTemplateAsset("Template_Tomato");
            template.EditorSetup("Tomato", mask, new[]
            {
                new ZoneRequirement { zoneName = "Tomatoes", channel = ZoneChannel.Red, suggestedPigment = palette[4], minCoverage = 0.5f, weight = 1f, missingPaintHint = "The tomatoes need a bit more paint." },
                new ZoneRequirement { zoneName = "Stem & leaves", channel = ZoneChannel.Green, suggestedPigment = palette[2], minCoverage = 0.5f, weight = 0.8f, missingPaintHint = "The stem and leaves need some color." },
                new ZoneRequirement { zoneName = "Stake", channel = ZoneChannel.Blue, suggestedPigment = palette[1], minCoverage = 0.5f, weight = 0.5f, missingPaintHint = "Don't forget the wooden stake." },
            });
            EditorUtility.SetDirty(template);

            var crop = GetOrCreateCropAsset("Crop_Tomato");
            crop.EditorSetup("tomato", "Tomato", template, 25f, BuildTomatoPlantPrefab(),
                PaintTemplateGenerator.GenerateTomatoIcon($"{Root}/Art/Textures/Icon_Tomato.png"), 15);
            crop.EditorSetPigmentYield(palette[4], 10);
            crop.EditorSetFavoriteSeason(Season.Autumn);
            crop.EditorSetVariants(new[]
            {
                new CropVariant { id = "golden", displayName = "Golden Tomato", zoneName = "Tomatoes", pigment = palette[0], rarity = Rarity.Uncommon },
                new CropVariant { id = "indigo", displayName = "Indigo Tomato", zoneName = "Tomatoes", pigment = palette[3], rarity = Rarity.Rare },
                new CropVariant { id = "ghost", displayName = "Ghost Tomato", zoneName = "Tomatoes", pigment = palette[5], rarity = Rarity.Rare },
            });
            EditorUtility.SetDirty(crop);
            return crop;
        }

        /// <summary>Plantilla y cultivo del glowbell, el primer cultivo fantástico (azul y blanco de la tienda).</summary>
        static CropDefinition GetOrCreateGlowbellCrop()
        {
            var palette = GetOrCreatePalette();
            var mask = PaintTemplateGenerator.GenerateGlowbellMask($"{Root}/Art/Textures/PaintTemplates/Glowbell_Zones.png");

            var template = GetOrCreateTemplateAsset("Template_Glowbell");
            template.EditorSetup("Glowbell", mask, new[]
            {
                new ZoneRequirement { zoneName = "Bells", channel = ZoneChannel.Red, suggestedPigment = palette[3], minCoverage = 0.5f, weight = 1f, missingPaintHint = "The bells need a bit more paint." },
                new ZoneRequirement { zoneName = "Glow", channel = ZoneChannel.Blue, suggestedPigment = palette[5], minCoverage = 0.5f, weight = 0.8f, missingPaintHint = "The glowing orbs under the bells are still empty." },
                new ZoneRequirement { zoneName = "Stem & leaves", channel = ZoneChannel.Green, suggestedPigment = palette[2], minCoverage = 0.5f, weight = 0.6f, missingPaintHint = "The stem and branches need some color." },
            });
            EditorUtility.SetDirty(template);

            var crop = GetOrCreateCropAsset("Crop_Glowbell");
            crop.EditorSetup("glowbell", "Glowbell", template, 30f, BuildGlowbellPlantPrefab(),
                PaintTemplateGenerator.GenerateGlowbellIcon($"{Root}/Art/Textures/Icon_Glowbell.png"), 25);
            crop.EditorSetPigmentYield(palette[3], 10);
            crop.EditorSetFavoriteSeason(Season.Winter);
            crop.EditorSetVariants(new[]
            {
                new CropVariant { id = "sun", displayName = "Sun Glowbell", zoneName = "Glow", pigment = palette[0], rarity = Rarity.Uncommon },
                new CropVariant { id = "ember", displayName = "Ember Glowbell", zoneName = "Glow", pigment = palette[4], rarity = Rarity.Rare },
            });
            EditorUtility.SetDirty(crop);
            return crop;
        }

        /// <summary>Plantilla y cultivo del sunbell, el primer híbrido (girasol + glowbell); no se vende, se aprende por polinización.</summary>
        static CropDefinition GetOrCreateSunbellCrop()
        {
            var palette = GetOrCreatePalette();
            var mask = PaintTemplateGenerator.GenerateSunbellMask($"{Root}/Art/Textures/PaintTemplates/Sunbell_Zones.png");

            var template = GetOrCreateTemplateAsset("Template_Sunbell");
            template.EditorSetup("Sunbell", mask, new[]
            {
                new ZoneRequirement { zoneName = "Petals", channel = ZoneChannel.Red, suggestedPigment = palette[0], minCoverage = 0.5f, weight = 1f, missingPaintHint = "The petals and bells need a bit more paint." },
                new ZoneRequirement { zoneName = "Glow", channel = ZoneChannel.Blue, suggestedPigment = palette[5], minCoverage = 0.5f, weight = 0.8f, missingPaintHint = "The glowing heart still needs paint." },
                new ZoneRequirement { zoneName = "Stem & leaves", channel = ZoneChannel.Green, suggestedPigment = palette[2], minCoverage = 0.5f, weight = 0.6f, missingPaintHint = "The stem and leaves need some color." },
            });
            EditorUtility.SetDirty(template);

            var crop = GetOrCreateCropAsset("Crop_Sunbell");
            crop.EditorSetup("sunbell", "Sunbell", template, 35f, BuildSunbellPlantPrefab(),
                PaintTemplateGenerator.GenerateSunbellIcon($"{Root}/Art/Textures/Icon_Sunbell.png"), 40);
            crop.EditorSetPigmentYield(palette[0], 10);
            crop.EditorSetFavoriteSeason(Season.Spring);
            crop.EditorSetVariants(System.Array.Empty<CropVariant>());
            EditorUtility.SetDirty(crop);
            return crop;
        }

        /// <summary>
        /// Sunbell procedural (placeholder) de ~1.2 m: girasol con una esfera luminosa en el centro (y una luz puntual
        /// suave) y dos campanillas colgando bajo los pétalos.
        /// </summary>
        static SunbellPlant BuildSunbellPlantPrefab()
        {
            var petalMat = GetOrCreateMaterial("M_Plant_Petal", new Color(0.98f, 0.78f, 0.15f));
            var bellMat = GetOrCreateMaterial("M_Plant_Bell", new Color(0.17f, 0.27f, 0.62f));
            var glowMat = GetOrCreateMaterial("M_Plant_Glow", new Color(0.98f, 0.98f, 0.96f));
            var stemMat = GetOrCreateMaterial("M_Plant_Stem", new Color(0.3f, 0.55f, 0.22f));

            var root = new GameObject("Sunbell");
            var growth = new GameObject("GrowthRoot").transform;
            growth.SetParent(root.transform, false);
            var stem = CreatePart(PrimitiveType.Cylinder, "Stem", growth, new Vector3(0f, 0.6f, 0f), new Vector3(0.045f, 0.6f, 0.045f), stemMat, Quaternion.identity);
            var stemRenderers = new System.Collections.Generic.List<Renderer> { stem.GetComponent<Renderer>() };

            var leafHinges = new Transform[2];
            float[] leafHeights = { 0.38f, 0.62f };
            float[] leafYaws = { 90f, -90f };
            for (int i = 0; i < 2; i++)
            {
                var hinge = new GameObject($"LeafHinge_{i}").transform;
                hinge.SetParent(growth, false);
                hinge.localPosition = new Vector3(0f, leafHeights[i], 0f);
                hinge.localRotation = Quaternion.Euler(0f, leafYaws[i], 0f);
                var leaf = CreatePart(PrimitiveType.Sphere, "Leaf", hinge, new Vector3(0f, 0f, 0.13f), new Vector3(0.09f, 0.015f, 0.26f), stemMat, Quaternion.identity);
                stemRenderers.Add(leaf.GetComponent<Renderer>());
                leafHinges[i] = hinge;
            }

            // Cabeza que mira a -Z (hacia quien coloca la parcela); el centro es una esfera luminosa.
            var head = new GameObject("Head").transform;
            head.SetParent(growth, false);
            head.localPosition = new Vector3(0f, 1.2f, 0f);
            head.localRotation = Quaternion.Euler(20f, 180f, 0f);
            var orb = CreatePart(PrimitiveType.Sphere, "Glow", head, new Vector3(0f, 0f, 0.03f), Vector3.one * 0.2f, glowMat, Quaternion.identity);
            var back = CreatePart(PrimitiveType.Cylinder, "Back", head, new Vector3(0f, 0f, -0.018f), new Vector3(0.24f, 0.015f, 0.24f), stemMat, Quaternion.Euler(90f, 0f, 0f));
            stemRenderers.Add(back.GetComponent<Renderer>());

            const int petalCount = 16;
            var petalHinges = new Transform[petalCount];
            var petalRenderers = new Renderer[petalCount];
            for (int i = 0; i < petalCount; i++)
            {
                var anchor = new GameObject($"PetalAnchor_{i}").transform;
                anchor.SetParent(head, false);
                anchor.localRotation = Quaternion.Euler(0f, 0f, i * 360f / petalCount);
                var hinge = new GameObject("Hinge").transform;
                hinge.SetParent(anchor, false);
                hinge.localPosition = new Vector3(0f, 0.1f, 0f);
                var petal = CreatePart(PrimitiveType.Sphere, "Petal", hinge, new Vector3(0f, 0.09f, 0f), new Vector3(0.06f, 0.18f, 0.012f), petalMat, Quaternion.identity);
                petalHinges[i] = hinge;
                petalRenderers[i] = petal.GetComponent<Renderer>();
            }

            // Dos campanillas pequeñas que cuelgan bajo la flor (hijas de GrowthRoot, no de la cabeza inclinada).
            float[] bellXs = { -0.15f, 0.15f };
            var bellPivots = new Transform[bellXs.Length];
            var bellRenderers = new Renderer[bellXs.Length * 2];
            for (int i = 0; i < bellXs.Length; i++)
            {
                var bell = new GameObject($"Bell_{i}").transform;
                bell.SetParent(growth, false);
                bell.localPosition = new Vector3(bellXs[i], 0.97f, -0.12f);
                var body = CreatePart(PrimitiveType.Sphere, "Body", bell, new Vector3(0f, -0.035f, 0f), new Vector3(0.06f, 0.08f, 0.06f), bellMat, Quaternion.identity);
                var rim = CreatePart(PrimitiveType.Sphere, "Rim", bell, new Vector3(0f, -0.075f, 0f), new Vector3(0.09f, 0.02f, 0.09f), bellMat, Quaternion.identity);
                bellRenderers[i * 2] = body.GetComponent<Renderer>();
                bellRenderers[i * 2 + 1] = rim.GetComponent<Renderer>();
                bellPivots[i] = bell;
            }

            var lightGo = new GameObject("GlowLight");
            lightGo.transform.SetParent(root.transform, false);
            lightGo.transform.localPosition = new Vector3(0f, 1.2f, -0.3f);
            var light = lightGo.AddComponent<Light>();
            light.type = LightType.Point;
            light.range = 2f;
            light.intensity = 0f;
            light.shadows = LightShadows.None;

            var plant = root.AddComponent<SunbellPlant>();
            var so = new SerializedObject(plant);
            so.FindProperty("growthRoot").objectReferenceValue = growth;
            so.FindProperty("head").objectReferenceValue = head;
            SetArray(so.FindProperty("leafHinges"), leafHinges);
            SetArray(so.FindProperty("petalHinges"), petalHinges);
            SetArray(so.FindProperty("petalRenderers"), petalRenderers);
            SetArray(so.FindProperty("bellPivots"), bellPivots);
            SetArray(so.FindProperty("bellRenderers"), bellRenderers);
            SetArray(so.FindProperty("glowRenderers"), new Object[] { orb.GetComponent<Renderer>() });
            SetArray(so.FindProperty("stemRenderers"), stemRenderers.ToArray());
            so.FindProperty("glowLight").objectReferenceValue = light;
            so.ApplyModifiedPropertiesWithoutUndo();

            UseLowPolySpheres(root);
            var prefab = PrefabUtility.SaveAsPrefabAsset(root, SunbellPrefabPath);
            Object.DestroyImmediate(root);
            return prefab.GetComponent<SunbellPlant>();
        }

        /// <summary>
        /// Glowbell procedural (placeholder) de ~0.85 m: tallo, dos hojas y cuatro ramas inclinadas; de la punta de
        /// cada rama cuelga una campanilla con una esfera luminosa. Una luz puntual suave ilumina alrededor.
        /// </summary>
        static GlowbellPlant BuildGlowbellPlantPrefab()
        {
            var bellMat = GetOrCreateMaterial("M_Plant_Bell", new Color(0.17f, 0.27f, 0.62f));
            var glowMat = GetOrCreateMaterial("M_Plant_Glow", new Color(0.98f, 0.98f, 0.96f));
            var stemMat = GetOrCreateMaterial("M_Plant_Stem", new Color(0.3f, 0.55f, 0.22f));

            var root = new GameObject("Glowbell");
            var growth = new GameObject("GrowthRoot").transform;
            growth.SetParent(root.transform, false);
            // Tallo de 0.85 m: termina justo encima de la rama más alta.
            var stem = CreatePart(PrimitiveType.Cylinder, "Stem", growth, new Vector3(0f, 0.425f, 0f), new Vector3(0.03f, 0.425f, 0.03f), stemMat, Quaternion.identity);
            var stemRenderers = new System.Collections.Generic.List<Renderer> { stem.GetComponent<Renderer>() };

            float[] leafHeights = { 0.15f, 0.22f };
            float[] leafYaws = { 90f, -90f };
            var leafHinges = new Transform[leafHeights.Length];
            for (int i = 0; i < leafHeights.Length; i++)
            {
                var hinge = new GameObject($"LeafHinge_{i}").transform;
                hinge.SetParent(growth, false);
                hinge.localPosition = new Vector3(0f, leafHeights[i], 0f);
                hinge.localRotation = Quaternion.Euler(0f, leafYaws[i], 0f);
                var leaf = CreatePart(PrimitiveType.Sphere, "Leaf", hinge, new Vector3(0f, 0f, 0.11f), new Vector3(0.08f, 0.012f, 0.22f), stemMat, Quaternion.identity);
                stemRenderers.Add(leaf.GetComponent<Renderer>());
                leafHinges[i] = hinge;
            }

            // (altura en el tallo, giro alrededor del tallo, largo). Giro 180 = hacia -Z, hacia quien la plantó.
            (float height, float yaw, float length)[] branches = { (0.55f, -150f, 0.3f), (0.7f, 150f, 0.28f), (0.8f, 30f, 0.25f), (0.62f, -40f, 0.27f) };
            const float tilt = 60f; // grados desde la vertical
            var branchPivots = new Transform[branches.Length];
            var bellPivots = new Transform[branches.Length];
            var bellRenderers = new System.Collections.Generic.List<Renderer>();
            var glowRenderers = new Renderer[branches.Length];
            for (int i = 0; i < branches.Length; i++)
            {
                var (height, yaw, length) = branches[i];
                var pivot = new GameObject($"Branch_{i}").transform;
                pivot.SetParent(growth, false);
                pivot.localPosition = new Vector3(0f, height, 0f);
                pivot.localRotation = Quaternion.Euler(0f, yaw, 0f) * Quaternion.Euler(tilt, 0f, 0f);
                var branch = CreatePart(PrimitiveType.Cylinder, "Branch", pivot, new Vector3(0f, length * 0.5f, 0f), new Vector3(0.015f, length * 0.5f, 0.015f), stemMat, Quaternion.identity);
                stemRenderers.Add(branch.GetComponent<Renderer>());
                branchPivots[i] = pivot;

                // La campanilla cuelga recta de la punta (hija de GrowthRoot, no de la rama inclinada).
                var bell = new GameObject($"Bell_{i}").transform;
                bell.SetParent(growth, false);
                bell.localPosition = pivot.localPosition + pivot.localRotation * new Vector3(0f, length, 0f);
                var body = CreatePart(PrimitiveType.Sphere, "Body", bell, new Vector3(0f, -0.07f, 0f), new Vector3(0.09f, 0.12f, 0.09f), bellMat, Quaternion.identity);
                var rim = CreatePart(PrimitiveType.Sphere, "Rim", bell, new Vector3(0f, -0.125f, 0f), new Vector3(0.13f, 0.03f, 0.13f), bellMat, Quaternion.identity);
                var orb = CreatePart(PrimitiveType.Sphere, "Glow", bell, new Vector3(0f, -0.165f, 0f), Vector3.one * 0.05f, glowMat, Quaternion.identity);
                bellRenderers.Add(body.GetComponent<Renderer>());
                bellRenderers.Add(rim.GetComponent<Renderer>());
                glowRenderers[i] = orb.GetComponent<Renderer>();
                bellPivots[i] = bell;
            }

            var lightGo = new GameObject("GlowLight");
            lightGo.transform.SetParent(root.transform, false);
            lightGo.transform.localPosition = new Vector3(0f, 0.55f, -0.1f);
            var light = lightGo.AddComponent<Light>();
            light.type = LightType.Point;
            light.range = 2f;
            light.intensity = 0f;
            light.shadows = LightShadows.None;

            var plant = root.AddComponent<GlowbellPlant>();
            var so = new SerializedObject(plant);
            so.FindProperty("growthRoot").objectReferenceValue = growth;
            SetArray(so.FindProperty("leafHinges"), leafHinges);
            SetArray(so.FindProperty("branchPivots"), branchPivots);
            SetArray(so.FindProperty("bellPivots"), bellPivots);
            SetArray(so.FindProperty("bellRenderers"), bellRenderers.ToArray());
            SetArray(so.FindProperty("glowRenderers"), glowRenderers);
            SetArray(so.FindProperty("stemRenderers"), stemRenderers.ToArray());
            so.FindProperty("glowLight").objectReferenceValue = light;
            so.ApplyModifiedPropertiesWithoutUndo();

            UseLowPolySpheres(root);
            var prefab = PrefabUtility.SaveAsPrefabAsset(root, GlowbellPrefabPath);
            Object.DestroyImmediate(root);
            return prefab.GetComponent<GlowbellPlant>();
        }

        /// <summary>
        /// Tomatera procedural (placeholder) de ~0.9 m junto a un tutor de 1.1 m: tallo, seis hojas con
        /// bisagra y cinco tomates (con cáliz) que cuelgan sobre todo hacia -Z. Los colores se ponen en runtime.
        /// </summary>
        static TomatoPlant BuildTomatoPlantPrefab()
        {
            var fruitMat = GetOrCreateMaterial("M_Plant_Tomato", new Color(0.75f, 0.15f, 0.17f));
            var stemMat = GetOrCreateMaterial("M_Plant_Stem", new Color(0.3f, 0.55f, 0.22f));
            var stakeMat = GetOrCreateMaterial("M_Plant_Stake", new Color(0.55f, 0.33f, 0.13f));

            var root = new GameObject("Tomato");
            // El tutor ya está clavado: no crece con la planta.
            var stake = CreatePart(PrimitiveType.Cylinder, "Stake", root.transform, new Vector3(0.16f, 0.55f, 0.06f), new Vector3(0.025f, 0.55f, 0.025f), stakeMat, Quaternion.identity);

            var growth = new GameObject("GrowthRoot").transform;
            growth.SetParent(root.transform, false);
            var stem = CreatePart(PrimitiveType.Cylinder, "Stem", growth, new Vector3(0f, 0.45f, 0f), new Vector3(0.03f, 0.45f, 0.03f), stemMat, Quaternion.identity);
            var leafRenderers = new System.Collections.Generic.List<Renderer> { stem.GetComponent<Renderer>() };

            float[] leafHeights = { 0.2f, 0.32f, 0.44f, 0.56f, 0.68f, 0.8f };
            float[] leafYaws = { 60f, -120f, 150f, -30f, 100f, -80f };
            var leafHinges = new Transform[leafHeights.Length];
            for (int i = 0; i < leafHeights.Length; i++)
            {
                var hinge = new GameObject($"LeafHinge_{i}").transform;
                hinge.SetParent(growth, false);
                hinge.localPosition = new Vector3(0f, leafHeights[i], 0f);
                hinge.localRotation = Quaternion.Euler(0f, leafYaws[i], 0f);
                var leaf = CreatePart(PrimitiveType.Sphere, "Leaf", hinge, new Vector3(0f, 0f, 0.1f), new Vector3(0.08f, 0.012f, 0.2f), stemMat, Quaternion.identity);
                leafRenderers.Add(leaf.GetComponent<Renderer>());
                leafHinges[i] = hinge;
            }

            Vector3[] fruitPositions =
            {
                new(-0.11f, 0.34f, -0.08f), new(0.09f, 0.46f, -0.1f), new(-0.07f, 0.6f, -0.11f),
                new(0.1f, 0.7f, 0.02f), new(-0.1f, 0.5f, 0.07f)
            };
            var fruitAnchors = new Transform[fruitPositions.Length];
            var fruitRenderers = new Renderer[fruitPositions.Length];
            for (int i = 0; i < fruitPositions.Length; i++)
            {
                var anchor = new GameObject($"FruitAnchor_{i}").transform;
                anchor.SetParent(growth, false);
                anchor.localPosition = fruitPositions[i];
                var fruit = CreatePart(PrimitiveType.Sphere, "Fruit", anchor, Vector3.zero, new Vector3(0.13f, 0.115f, 0.13f), fruitMat, Quaternion.identity);
                var calyx = CreatePart(PrimitiveType.Sphere, "Calyx", anchor, new Vector3(0f, 0.055f, 0f), new Vector3(0.07f, 0.015f, 0.07f), stemMat, Quaternion.identity);
                fruitAnchors[i] = anchor;
                fruitRenderers[i] = fruit.GetComponent<Renderer>();
                leafRenderers.Add(calyx.GetComponent<Renderer>());
            }

            var plant = root.AddComponent<TomatoPlant>();
            var so = new SerializedObject(plant);
            so.FindProperty("growthRoot").objectReferenceValue = growth;
            SetArray(so.FindProperty("leafHinges"), leafHinges);
            SetArray(so.FindProperty("fruitAnchors"), fruitAnchors);
            SetArray(so.FindProperty("fruitRenderers"), fruitRenderers);
            SetArray(so.FindProperty("leafRenderers"), leafRenderers.ToArray());
            SetArray(so.FindProperty("stakeRenderers"), new Object[] { stake.GetComponent<Renderer>() });
            so.ApplyModifiedPropertiesWithoutUndo();

            UseLowPolySpheres(root);
            var prefab = PrefabUtility.SaveAsPrefabAsset(root, TomatoPrefabPath);
            Object.DestroyImmediate(root);
            return prefab.GetComponent<TomatoPlant>();
        }

        /// <summary>Plantilla y cultivo del girasol (máscara de zonas regenerada cada vez).</summary>
        static CropDefinition GetOrCreateSunflowerCrop()
        {
            var palette = GetOrCreatePalette();
            var mask = PaintTemplateGenerator.GenerateSunflowerMask($"{Root}/Art/Textures/PaintTemplates/Sunflower_Zones.png");

            var templatePath = $"{Root}/Data/Templates/Template_Sunflower.asset";
            var template = AssetDatabase.LoadAssetAtPath<PaintTemplate>(templatePath);
            if (template == null)
            {
                template = ScriptableObject.CreateInstance<PaintTemplate>();
                AssetDatabase.CreateAsset(template, templatePath);
            }
            template.EditorSetup("Sunflower", mask, new[]
            {
                new ZoneRequirement { zoneName = "Petals", channel = ZoneChannel.Red, suggestedPigment = palette[0], minCoverage = 0.5f, weight = 1f, missingPaintHint = "The petals need a bit more paint." },
                new ZoneRequirement { zoneName = "Center", channel = ZoneChannel.Blue, suggestedPigment = palette[1], minCoverage = 0.5f, weight = 1f, missingPaintHint = "The center of the flower is still empty." },
                new ZoneRequirement { zoneName = "Stem & leaves", channel = ZoneChannel.Green, suggestedPigment = palette[2], minCoverage = 0.5f, weight = 0.8f, missingPaintHint = "The stem and leaves need some color." },
            });
            EditorUtility.SetDirty(template);

            var cropPath = $"{Root}/Data/Crops/Crop_Sunflower.asset";
            var crop = AssetDatabase.LoadAssetAtPath<CropDefinition>(cropPath);
            if (crop == null)
            {
                crop = ScriptableObject.CreateInstance<CropDefinition>();
                AssetDatabase.CreateAsset(crop, cropPath);
            }
            crop.EditorSetup("sunflower", "Sunflower", template, 20f, BuildSunflowerPlantPrefab(),
                PaintTemplateGenerator.GenerateSunflowerIcon($"{Root}/Art/Textures/Icon_Sunflower.png"), 10);
            crop.EditorSetPigmentYield(palette[0], 10);
            crop.EditorSetFavoriteSeason(Season.Summer);
            crop.EditorSetVariants(new[]
            {
                new CropVariant { id = "red", displayName = "Red Sunflower", zoneName = "Petals", pigment = palette[4], rarity = Rarity.Uncommon },
                new CropVariant { id = "blue", displayName = "Blue Sunflower", zoneName = "Petals", pigment = palette[3], rarity = Rarity.Rare },
                new CropVariant { id = "moon", displayName = "Moon Sunflower", zoneName = "Petals", pigment = palette[5], rarity = Rarity.Rare },
            });
            EditorUtility.SetDirty(crop);
            return crop;
        }

        /// <summary>
        /// Girasol procedural (placeholder) de ~1.2 m: tallo, dos hojas con bisagra y una cabeza que mira
        /// hacia -Z (hacia quien coloca la parcela) con 16 pétalos con bisagra. Los colores se ponen en runtime.
        /// </summary>
        static SunflowerPlant BuildSunflowerPlantPrefab()
        {
            var petalMat = GetOrCreateMaterial("M_Plant_Petal", new Color(0.98f, 0.78f, 0.15f));
            var centerMat = GetOrCreateMaterial("M_Plant_Center", new Color(0.45f, 0.3f, 0.15f));
            var stemMat = GetOrCreateMaterial("M_Plant_Stem", new Color(0.3f, 0.55f, 0.22f));

            var root = new GameObject("Sunflower");
            var growth = new GameObject("GrowthRoot").transform;
            growth.SetParent(root.transform, false);

            var stem = CreatePart(PrimitiveType.Cylinder, "Stem", growth, new Vector3(0f, 0.6f, 0f), new Vector3(0.045f, 0.6f, 0.045f), stemMat, Quaternion.identity);
            var stemRenderers = new System.Collections.Generic.List<Renderer> { stem.GetComponent<Renderer>() };

            var leafHinges = new Transform[2];
            float[] leafHeights = { 0.38f, 0.62f };
            float[] leafYaws = { 90f, -90f };
            for (int i = 0; i < 2; i++)
            {
                var hinge = new GameObject($"LeafHinge_{i}").transform;
                hinge.SetParent(growth, false);
                hinge.localPosition = new Vector3(0f, leafHeights[i], 0f);
                hinge.localRotation = Quaternion.Euler(0f, leafYaws[i], 0f);
                var leaf = CreatePart(PrimitiveType.Sphere, "Leaf", hinge, new Vector3(0f, 0f, 0.13f), new Vector3(0.09f, 0.015f, 0.26f), stemMat, Quaternion.identity);
                stemRenderers.Add(leaf.GetComponent<Renderer>());
                leafHinges[i] = hinge;
            }

            var head = new GameObject("Head").transform;
            head.SetParent(growth, false);
            head.localPosition = new Vector3(0f, 1.2f, 0f);
            head.localRotation = Quaternion.Euler(20f, 180f, 0f);
            var center = CreatePart(PrimitiveType.Cylinder, "Center", head, new Vector3(0f, 0f, 0.012f), new Vector3(0.22f, 0.02f, 0.22f), centerMat, Quaternion.Euler(90f, 0f, 0f));
            var back = CreatePart(PrimitiveType.Cylinder, "Back", head, new Vector3(0f, 0f, -0.018f), new Vector3(0.24f, 0.015f, 0.24f), stemMat, Quaternion.Euler(90f, 0f, 0f));
            stemRenderers.Add(back.GetComponent<Renderer>());

            const int petalCount = 16;
            var petalHinges = new Transform[petalCount];
            var petalRenderers = new Renderer[petalCount];
            for (int i = 0; i < petalCount; i++)
            {
                var anchor = new GameObject($"PetalAnchor_{i}").transform;
                anchor.SetParent(head, false);
                anchor.localRotation = Quaternion.Euler(0f, 0f, i * 360f / petalCount);
                var hinge = new GameObject("Hinge").transform;
                hinge.SetParent(anchor, false);
                hinge.localPosition = new Vector3(0f, 0.1f, 0f);
                var petal = CreatePart(PrimitiveType.Sphere, "Petal", hinge, new Vector3(0f, 0.09f, 0f), new Vector3(0.06f, 0.18f, 0.012f), petalMat, Quaternion.identity);
                petalHinges[i] = hinge;
                petalRenderers[i] = petal.GetComponent<Renderer>();
            }

            var plant = root.AddComponent<SunflowerPlant>();
            var so = new SerializedObject(plant);
            so.FindProperty("growthRoot").objectReferenceValue = growth;
            so.FindProperty("head").objectReferenceValue = head;
            SetArray(so.FindProperty("leafHinges"), leafHinges);
            SetArray(so.FindProperty("petalHinges"), petalHinges);
            SetArray(so.FindProperty("petalRenderers"), petalRenderers);
            SetArray(so.FindProperty("centerRenderers"), new Object[] { center.GetComponent<Renderer>() });
            SetArray(so.FindProperty("stemRenderers"), stemRenderers.ToArray());
            so.ApplyModifiedPropertiesWithoutUndo();

            UseLowPolySpheres(root);
            var prefab = PrefabUtility.SaveAsPrefabAsset(root, SunflowerPrefabPath);
            Object.DestroyImmediate(root);
            return prefab.GetComponent<SunflowerPlant>();
        }

        /// <summary>Gestor de guardado: autoguarda y carga la partida; su registro lleva todos los assets de datos para resolver ids.</summary>
        static SaveManager BuildSaveManager(GameObject player)
        {
            var saveManager = new GameObject("SaveManager").AddComponent<SaveManager>();
            var so = new SerializedObject(saveManager);
            so.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
            so.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
            so.FindProperty("inventory").objectReferenceValue = player.GetComponent<PlayerInventory>();
            var registry = so.FindProperty("registry");
            SetArray(registry.FindPropertyRelative("crops"), FindDataAssets<CropDefinition>());
            SetArray(registry.FindPropertyRelative("pigments"), FindDataAssets<PigmentDefinition>());
            SetArray(registry.FindPropertyRelative("brushes"), FindDataAssets<BrushDefinition>());
            SetArray(registry.FindPropertyRelative("styles"), FindDataAssets<StyleDefinition>());
            SetArray(registry.FindPropertyRelative("canvasTypes"), FindDataAssets<CanvasType>());
            SetArray(registry.FindPropertyRelative("sets"), FindDataAssets<CollectionSet>());
            so.ApplyModifiedPropertiesWithoutUndo();
            return saveManager;
        }

        /// <summary>Música y efectos de sonido; antes ajusta cómo se importan los audios (música en streaming, efectos descomprimidos).</summary>
        static void BuildAudio(GameObject player, SeasonClock seasonClock)
        {
            const string musicDir = "Assets/_TheLivingCanvas/Audio/Music/";
            const string sfxDir = "Assets/_TheLivingCanvas/Audio/Sfx/";
            foreach (var guid in AssetDatabase.FindAssets("t:AudioClip", new[] { musicDir }))
                SetAudioImport(AssetDatabase.GUIDToAssetPath(guid), AudioClipLoadType.Streaming);
            foreach (var guid in AssetDatabase.FindAssets("t:AudioClip", new[] { sfxDir }))
                SetAudioImport(AssetDatabase.GUIDToAssetPath(guid), AudioClipLoadType.DecompressOnLoad);

            var audio = new GameObject("Audio");
            // Se desactiva mientras se cablea: los Awake/OnEnable necesitan las referencias ya puestas.
            audio.SetActive(false);
            var sfx = audio.AddComponent<SfxPlayer>();
            var sfxSo = new SerializedObject(sfx);
            sfxSo.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
            sfxSo.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
            sfxSo.FindProperty("inventory").objectReferenceValue = player.GetComponent<PlayerInventory>();
            sfxSo.FindProperty("brushLoop").objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(sfxDir + "brush_loop.wav");
            sfxSo.FindProperty("paintFinish").objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(sfxDir + "paint_finish.wav");
            sfxSo.FindProperty("harvest").objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(sfxDir + "harvest.wav");
            sfxSo.FindProperty("coin").objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(sfxDir + "coin.wav");
            sfxSo.FindProperty("uiOpen").objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(sfxDir + "ui_open.wav");
            sfxSo.FindProperty("uiClose").objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(sfxDir + "ui_close.wav");
            sfxSo.FindProperty("place").objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(sfxDir + "place.wav");
            sfxSo.FindProperty("levelUp").objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(sfxDir + "level_up.wav");
            sfxSo.ApplyModifiedPropertiesWithoutUndo();

            var music = audio.AddComponent<MusicPlayer>();
            var musicSo = new SerializedObject(music);
            musicSo.FindProperty("seasons").objectReferenceValue = seasonClock;
            musicSo.FindProperty("dayTrack").objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(musicDir + "the_garden_remembers.ogg");
            musicSo.FindProperty("eveningTrack").objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(musicDir + "embers_and_lamplight.ogg");
            musicSo.ApplyModifiedPropertiesWithoutUndo();
            audio.SetActive(true);
        }

        /// <summary>Objeto "Feedback": las pinceladas de partículas (material M_PaintDabs, con el atlas T_PaintDabs).</summary>
        static void BuildFeedback()
        {
            const string vfxDir = Root + "/Art/VFX/";
            var texturePath = vfxDir + "T_PaintDabs.png";
            // Las pinceladas son blancas con alfa: sin "alpha is transparency" el borde sangraría un halo blanco.
            if (AssetImporter.GetAtPath(texturePath) is TextureImporter importer && (!importer.alphaIsTransparency || !importer.sRGBTexture))
            {
                importer.alphaIsTransparency = true;
                importer.sRGBTexture = true;
                importer.SaveAndReimport();
            }

            var materialPath = vfxDir + "M_PaintDabs.mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            if (material == null)
            {
                material = new Material(Shader.Find("Universal Render Pipeline/Particles/Unlit"));
                AssetDatabase.CreateAsset(material, materialPath);
            }
            // Transparente con mezcla alfa, sin escribir en Z (lo que hacen las claves de URP al elegir Surface Type: Transparent).
            material.SetFloat("_Surface", 1f);
            material.SetFloat("_Blend", 0f);
            material.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
            material.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            material.SetFloat("_ZWrite", 0f);
            material.SetOverrideTag("RenderType", "Transparent");
            material.SetShaderPassEnabled("ShadowCaster", false);
            material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            material.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            material.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath));
            material.SetColor("_BaseColor", Color.white);
            EditorUtility.SetDirty(material);

            var feedback = new GameObject("Feedback");
            feedback.SetActive(false);
            var burst = feedback.AddComponent<PaintBurst>();
            var burstSo = new SerializedObject(burst);
            burstSo.FindProperty("dabMaterial").objectReferenceValue = material;
            burstSo.ApplyModifiedPropertiesWithoutUndo();
            feedback.SetActive(true);
        }

        /// <summary>Aplica tipo de carga y Vorbis al audio solo si difiere, para no reimportar sin necesidad.</summary>
        static void SetAudioImport(string path, AudioClipLoadType loadType)
        {
            if (AssetImporter.GetAtPath(path) is not AudioImporter importer) return;
            var settings = importer.defaultSampleSettings;
            if (settings.loadType == loadType && settings.compressionFormat == AudioCompressionFormat.Vorbis) return;
            settings.loadType = loadType;
            settings.compressionFormat = AudioCompressionFormat.Vorbis;
            importer.defaultSampleSettings = settings;
            importer.SaveAndReimport();
        }

        /// <summary>
        /// Menú de pausa (Esc / Start): panel centrado con sensibilidad, volumen, pantalla completa y los botones
        /// Resume / New game / Quit; la X de la esquina es el botón Close que pide ModalPanel.
        /// </summary>
        static void BuildPauseMenu(Transform hud, GameObject player, GameObject rig, PaintModeController paintMode,
            PaintingPlacer placer, SaveManager saveManager)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var cream = new Color(1f, 0.95f, 0.82f);
            var uiSprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");
            var resources = new DefaultControls.Resources
            {
                standard = uiSprite,
                background = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Background.psd"),
                knob = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Knob.psd")
            };

            var root = new GameObject("PauseMenu", typeof(RectTransform));
            root.transform.SetParent(hud, false);
            var rootRect = (RectTransform)root.transform;
            rootRect.anchorMin = Vector2.zero;
            rootRect.anchorMax = Vector2.one;
            rootRect.offsetMin = rootRect.offsetMax = Vector2.zero;

            var panel = CreatePanel(root.transform, "Panel", uiSprite, new Color(0.30f, 0.20f, 0.13f, 0.95f),
                new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(480f, 710f));
            panel.AddComponent<FitToScreenHeight>();
            panel.GetComponent<Image>().raycastTarget = true; // los clics no atraviesan el panel
            var layout = panel.AddComponent<VerticalLayoutGroup>();
            layout.padding = new RectOffset(24, 24, 24, 24);
            layout.spacing = 14f;
            layout.childAlignment = TextAnchor.UpperCenter;
            layout.childControlWidth = layout.childControlHeight = true;
            layout.childForceExpandWidth = true;
            layout.childForceExpandHeight = false;

            AddLabel(panel.transform, "Title", "Paused", 34, 44f, font, cream);

            AddLabel(panel.transform, "SensitivityLabel", "Mouse sensitivity", 24, 30f, font, cream);
            var sensitivity = DefaultControls.CreateSlider(resources);
            sensitivity.name = "SensitivitySlider";
            sensitivity.transform.SetParent(panel.transform, false);
            sensitivity.AddComponent<LayoutElement>().preferredHeight = 30f;

            AddLabel(panel.transform, "VolumeLabel", "Volume", 24, 30f, font, cream);
            var volume = DefaultControls.CreateSlider(resources);
            volume.name = "VolumeSlider";
            volume.transform.SetParent(panel.transform, false);
            volume.AddComponent<LayoutElement>().preferredHeight = 30f;

            AddLabel(panel.transform, "UiScaleLabel", "Interface size", 24, 30f, font, cream);
            var uiScale = DefaultControls.CreateSlider(resources);
            uiScale.name = "UiScaleSlider";
            uiScale.transform.SetParent(panel.transform, false);
            uiScale.AddComponent<LayoutElement>().preferredHeight = 30f;

            var fullscreen = DefaultControls.CreateToggle(resources);
            fullscreen.name = "FullscreenToggle";
            fullscreen.transform.SetParent(panel.transform, false);
            fullscreen.AddComponent<LayoutElement>().preferredHeight = 40f;
            var fullscreenLabel = fullscreen.GetComponentInChildren<Text>();
            fullscreenLabel.text = "Fullscreen";
            fullscreenLabel.font = font;
            fullscreenLabel.fontSize = 24;
            fullscreenLabel.color = cream;

            var resume = CreateButton(resources, panel.transform, "ResumeButton", "Resume", 24, font);
            var controls = CreateButton(resources, panel.transform, "ControlsButton", "Controls", 24, font);
            var newGame = CreateButton(resources, panel.transform, "NewGameButton", "New game", 24, font);
            var quit = CreateButton(resources, panel.transform, "QuitButton", "Quit game", 24, font);

            var close = CreateButton(resources, panel.transform, "Close", "X", 24, font);
            close.GetComponent<LayoutElement>().ignoreLayout = true;
            var closeRect = (RectTransform)close.transform;
            closeRect.anchorMin = closeRect.anchorMax = closeRect.pivot = new Vector2(1f, 1f);
            closeRect.anchoredPosition = new Vector2(-12f, -12f);
            closeRect.sizeDelta = new Vector2(44f, 44f);

            var (controlsPanel, controlsBack) = BuildControlsPanel(panel.transform, uiSprite, resources, font, cream);

            var pauseMenu = root.AddComponent<PauseMenu>();
            var so = new SerializedObject(pauseMenu);
            SetModalBaseRefs(so, panel, close.GetComponent<Button>(), player, rig);
            so.FindProperty("paintMode").objectReferenceValue = paintMode;
            so.FindProperty("placer").objectReferenceValue = placer;
            so.FindProperty("saveManager").objectReferenceValue = saveManager;
            so.FindProperty("sensitivitySlider").objectReferenceValue = sensitivity.GetComponent<Slider>();
            so.FindProperty("volumeSlider").objectReferenceValue = volume.GetComponent<Slider>();
            so.FindProperty("uiScaleSlider").objectReferenceValue = uiScale.GetComponent<Slider>();
            so.FindProperty("fullscreenToggle").objectReferenceValue = fullscreen.GetComponent<Toggle>();
            so.FindProperty("controlsButton").objectReferenceValue = controls.GetComponent<Button>();
            so.FindProperty("controlsPanel").objectReferenceValue = controlsPanel;
            so.FindProperty("controlsBackButton").objectReferenceValue = controlsBack.GetComponent<Button>();
            so.FindProperty("resumeButton").objectReferenceValue = resume.GetComponent<Button>();
            so.FindProperty("newGameButton").objectReferenceValue = newGame.GetComponent<Button>();
            so.FindProperty("newGameLabel").objectReferenceValue = newGame.GetComponentInChildren<Text>();
            so.FindProperty("quitButton").objectReferenceValue = quit.GetComponent<Button>();
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>
        /// Lista de controles (de PlayerControls.inputactions) encima del menú de pausa: tres columnas alineadas
        /// línea a línea (acción, teclado y ratón, mando) y un botón Back.
        /// </summary>
        static (GameObject panel, GameObject backButton) BuildControlsPanel(Transform pausePanel, Sprite uiSprite,
            DefaultControls.Resources resources, Font font, Color cream)
        {
            var panel = CreatePanel(pausePanel, "ControlsPanel", uiSprite, new Color(0.30f, 0.20f, 0.13f, 1f),
                new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(780f, 700f));
            panel.GetComponent<Image>().raycastTarget = true; // tapa el menú y los clics no lo atraviesan
            panel.AddComponent<LayoutElement>().ignoreLayout = true;
            var layout = panel.AddComponent<VerticalLayoutGroup>();
            layout.padding = new RectOffset(30, 30, 24, 24);
            layout.spacing = 14f;
            layout.childAlignment = TextAnchor.UpperCenter;
            layout.childControlWidth = layout.childControlHeight = true;
            layout.childForceExpandWidth = true;
            layout.childForceExpandHeight = false;

            AddLabel(panel.transform, "Title", "Controls", 34, 44f, font, cream);

            var columns = new GameObject("Columns", typeof(RectTransform), typeof(HorizontalLayoutGroup), typeof(LayoutElement));
            columns.transform.SetParent(panel.transform, false);
            columns.GetComponent<LayoutElement>().flexibleHeight = 1f;
            var row = columns.GetComponent<HorizontalLayoutGroup>();
            row.spacing = 16f;
            row.childControlWidth = row.childControlHeight = true;
            row.childForceExpandWidth = row.childForceExpandHeight = false;

            // Cada columna es un solo texto; las líneas en blanco separan secciones y mantienen las filas alineadas.
            AddControlsColumn(columns.transform, "Actions", 230f, font, cream,
                "<b>Action</b>\nMove\nLook\nSprint\nInteract\nInventory\nCalendar\nPause menu\n\n<b>Painting</b>\nPaint\nBrush size\nUndo\nRedo\nExit painting");
            AddControlsColumn(columns.transform, "Keyboard", 280f, font, cream,
                "<b>Keyboard / Mouse</b>\nW A S D\nMouse\nLeft Shift\nE\nI or Tab\nC\nEsc\n\n \nLeft mouse button\nMouse wheel or [ ]\nCtrl + Z\nCtrl + Y\nEsc or E");
            AddControlsColumn(columns.transform, "Gamepad", 200f, font, cream,
                "<b>Gamepad</b>\nLeft stick\nRight stick\nLeft stick click\nA\nY\nD-pad up\nStart\n\n \n-\n-\n-\n-\nB or A");

            var back = CreateButton(resources, panel.transform, "BackButton", "Back", 24, font);
            return (panel, back);
        }

        static void AddControlsColumn(Transform parent, string name, float width, Font font, Color color, string content)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Text), typeof(LayoutElement));
            go.transform.SetParent(parent, false);
            go.GetComponent<LayoutElement>().preferredWidth = width;
            var text = go.GetComponent<Text>();
            text.text = content;
            text.font = font;
            text.fontSize = 22;
            text.alignment = TextAnchor.UpperLeft;
            text.color = color;
            text.horizontalOverflow = HorizontalWrapMode.Overflow; // una línea por fila, sin saltos que descuadren las columnas
            text.raycastTarget = false;
        }

        /// <summary>Todos los assets de un tipo bajo Data/ (incluye los que no salen de las listas GetOrCreate*: violeta, de temporada, oro, híbrido).</summary>
        static T[] FindDataAssets<T>() where T : Object =>
            AssetDatabase.FindAssets($"t:{typeof(T).Name}", new[] { Root + "/Data" })
                .Select(guid => AssetDatabase.GUIDToAssetPath(guid)).OrderBy(path => path)
                .Select(path => AssetDatabase.LoadAssetAtPath<T>(path)).ToArray();

        static void SetArray(SerializedProperty property, Object[] values)
        {
            property.arraySize = values.Length;
            for (int i = 0; i < values.Length; i++)
                property.GetArrayElementAtIndex(i).objectReferenceValue = values[i];
        }

        static PigmentDefinition GetOrCreatePigment(string id, string displayName, Color color)
        {
            var path = $"{Root}/Data/Pigments/Pigment_{id}.asset";
            var pigment = AssetDatabase.LoadAssetAtPath<PigmentDefinition>(path);
            if (pigment == null)
            {
                pigment = ScriptableObject.CreateInstance<PigmentDefinition>();
                AssetDatabase.CreateAsset(pigment, path);
            }
            pigment.EditorSetup(id, displayName, color);
            EditorUtility.SetDirty(pigment);
            return pigment;
        }

        /// <summary>
        /// Caballete placeholder con un lienzo de 1 × 0.8 m inclinado hacia atrás.
        /// El frente (+Z local) mira al pintor; ViewPoint queda perpendicular al lienzo.
        /// </summary>
        static GameObject BuildEaselPrefab()
        {
            var woodMat = GetOrCreateMaterial("M_Easel_Wood", new Color(0.42f, 0.28f, 0.18f));
            var canvasMat = GetOrCreateMaterial("M_Canvas_Blank", new Color(0.96f, 0.94f, 0.88f));

            var root = new GameObject("Easel");
            var blocker = root.AddComponent<BoxCollider>();
            blocker.center = new Vector3(0f, 0.9f, 0f);
            blocker.size = new Vector3(1.2f, 1.8f, 0.6f);

            CreatePart(PrimitiveType.Cube, "Leg_Left", root.transform, new Vector3(-0.45f, 0.8f, 0.1f), new Vector3(0.05f, 1.6f, 0.05f), woodMat, Quaternion.Euler(-8f, 0f, 4f));
            CreatePart(PrimitiveType.Cube, "Leg_Right", root.transform, new Vector3(0.45f, 0.8f, 0.1f), new Vector3(0.05f, 1.6f, 0.05f), woodMat, Quaternion.Euler(-8f, 0f, -4f));
            CreatePart(PrimitiveType.Cube, "Leg_Back", root.transform, new Vector3(0f, 0.75f, -0.3f), new Vector3(0.05f, 1.5f, 0.05f), woodMat, Quaternion.Euler(20f, 0f, 0f));
            CreatePart(PrimitiveType.Cube, "Ledge", root.transform, new Vector3(0f, 0.9f, 0.14f), new Vector3(1.1f, 0.04f, 0.1f), woodMat, Quaternion.identity);

            // Tablero inclinado 8° hacia atrás; el lienzo y el punto de vista cuelgan de él.
            var board = new GameObject("Board").transform;
            board.SetParent(root.transform, false);
            board.localPosition = new Vector3(0f, 1.32f, 0.08f);
            board.localRotation = Quaternion.Euler(-8f, 0f, 0f);

            CreatePart(PrimitiveType.Cube, "Frame", board, new Vector3(0f, 0f, -0.02f), new Vector3(1.06f, 0.86f, 0.03f), woodMat, Quaternion.identity);
            var canvas = CreatePart(PrimitiveType.Quad, "Canvas", board, Vector3.zero, new Vector3(1f, 0.8f, 1f), canvasMat, Quaternion.Euler(0f, 180f, 0f));
            canvas.transform.localPosition = new Vector3(0f, 0f, 0.001f);
            var surface = canvas.AddComponent<PaintSurface>();
            var guide = canvas.AddComponent<CanvasGuide>();

            var viewPoint = new GameObject("ViewPoint").transform;
            viewPoint.SetParent(board, false);
            viewPoint.localPosition = new Vector3(0f, 0f, 1.15f);
            viewPoint.localRotation = Quaternion.Euler(0f, 180f, 0f);

            var interactable = root.AddComponent<CanvasInteractable>();
            var so = new SerializedObject(interactable);
            so.FindProperty("viewPoint").objectReferenceValue = viewPoint;
            so.FindProperty("surface").objectReferenceValue = surface;
            so.FindProperty("guide").objectReferenceValue = guide;
            so.ApplyModifiedPropertiesWithoutUndo();

            var prefab = PrefabUtility.SaveAsPrefabAsset(root, EaselPrefabPath);
            Object.DestroyImmediate(root);
            return prefab;
        }

        const string LowSpherePath = Root + "/Art/Models/LowSphere.asset";

        /// <summary>
        /// Las plantas usan muchas esferas pequeñas (pétalos, frutos, campanillas): la esfera de Unity tiene 768 triángulos,
        /// demasiados para un jardín lleno. Las cambia por una esfera de baja resolución (~100 triángulos).
        /// </summary>
        static void UseLowPolySpheres(GameObject root)
        {
            var low = GetOrCreateLowSphere();
            foreach (var filter in root.GetComponentsInChildren<MeshFilter>(true))
                if (filter.sharedMesh != null && filter.sharedMesh.name == "Sphere")
                    filter.sharedMesh = low;
        }

        /// <summary>Esfera UV de radio 0.5 (como la de Unity) con 10 segmentos y 6 anillos, guardada como asset.</summary>
        static Mesh GetOrCreateLowSphere()
        {
            var existing = AssetDatabase.LoadAssetAtPath<Mesh>(LowSpherePath);
            if (existing != null) return existing;

            const int segments = 10, rings = 6;
            var vertices = new List<Vector3>();
            var normals = new List<Vector3>();
            var uvs = new List<Vector2>();
            for (int r = 0; r <= rings; r++)
            {
                float v = (float)r / rings;
                float phi = v * Mathf.PI;
                for (int s = 0; s <= segments; s++)
                {
                    float u = (float)s / segments;
                    float theta = u * 2f * Mathf.PI;
                    var n = new Vector3(Mathf.Sin(phi) * Mathf.Cos(theta), Mathf.Cos(phi), Mathf.Sin(phi) * Mathf.Sin(theta));
                    vertices.Add(n * 0.5f);
                    normals.Add(n);
                    uvs.Add(new Vector2(u, 1f - v));
                }
            }
            var triangles = new List<int>();
            for (int r = 0; r < rings; r++)
                for (int s = 0; s < segments; s++)
                {
                    int a = r * (segments + 1) + s, c = a + segments + 1;
                    if (r > 0) triangles.AddRange(new[] { a, a + 1, c });
                    if (r < rings - 1) triangles.AddRange(new[] { a + 1, c + 1, c });
                }
            var mesh = new Mesh { name = "LowSphere" };
            mesh.SetVertices(vertices);
            mesh.SetNormals(normals);
            mesh.SetUVs(0, uvs);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateBounds();
            Directory.CreateDirectory(Path.GetDirectoryName(LowSpherePath));
            AssetDatabase.CreateAsset(mesh, LowSpherePath);
            return mesh;
        }

        static GameObject CreatePart(PrimitiveType type, string name, Transform parent, Vector3 position, Vector3 scale, Material material, Quaternion rotation)
        {
            var go = GameObject.CreatePrimitive(type);
            go.name = name;
            if (type != PrimitiveType.Quad)
                Object.DestroyImmediate(go.GetComponent<Collider>()); // el BoxCollider del caballete basta
            go.transform.SetParent(parent, false);
            go.transform.localPosition = position;
            go.transform.localRotation = rotation;
            go.transform.localScale = scale;
            go.GetComponent<MeshRenderer>().sharedMaterial = material;
            return go;
        }

        /// <summary>HUD provisional: aviso de interacción abajo al centro.</summary>
        static GameObject BuildHud(PlayerInteractor interactor)
        {
            var hud = new GameObject("HUD");
            hud.AddComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = hud.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.matchWidthOrHeight = 0.5f;
            hud.AddComponent<UiScaleApplier>(); // aplica el tamaño de interfaz de las opciones
            hud.AddComponent<GraphicRaycaster>(); // necesario para que los botones reciban clics

            var panel = new GameObject("InteractionPrompt", typeof(RectTransform), typeof(Image));
            panel.transform.SetParent(hud.transform, false);
            var panelRect = (RectTransform)panel.transform;
            panelRect.anchorMin = panelRect.anchorMax = panelRect.pivot = new Vector2(0.5f, 0f);
            panelRect.anchoredPosition = new Vector2(0f, 120f);
            panelRect.sizeDelta = new Vector2(520f, 64f);
            panel.GetComponent<Image>().color = new Color(0.16f, 0.11f, 0.08f, 0.75f);

            var labelGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
            labelGo.transform.SetParent(panel.transform, false);
            var labelRect = (RectTransform)labelGo.transform;
            labelRect.anchorMin = Vector2.zero;
            labelRect.anchorMax = Vector2.one;
            labelRect.offsetMin = labelRect.offsetMax = Vector2.zero;
            var label = labelGo.GetComponent<Text>();
            label.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            label.fontSize = 30;
            label.alignment = TextAnchor.MiddleCenter;
            label.color = new Color(1f, 0.95f, 0.85f);

            // Mira de primera persona: un punto redondo en el centro.
            var reticleGo = new GameObject("Reticle", typeof(RectTransform), typeof(Image));
            reticleGo.transform.SetParent(hud.transform, false);
            var reticleRect = (RectTransform)reticleGo.transform;
            reticleRect.anchorMin = reticleRect.anchorMax = reticleRect.pivot = new Vector2(0.5f, 0.5f);
            reticleRect.sizeDelta = new Vector2(10f, 10f);
            var reticle = reticleGo.GetComponent<Image>();
            reticle.sprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Knob.psd");
            reticle.raycastTarget = false;

            var promptUi = hud.AddComponent<InteractionPromptUI>();
            var so = new SerializedObject(promptUi);
            so.FindProperty("interactor").objectReferenceValue = interactor;
            so.FindProperty("panel").objectReferenceValue = panel;
            so.FindProperty("label").objectReferenceValue = label;
            so.FindProperty("reticle").objectReferenceValue = reticle;
            so.ApplyModifiedPropertiesWithoutUndo();
            panel.SetActive(false);
            return hud;
        }

        /// <summary>Monedas arriba a la derecha, con el "+30" debajo.</summary>
        static void BuildCoinCounter(Transform hud, Wallet wallet)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var cream = new Color(1f, 0.95f, 0.82f);
            var panel = CreatePanel(hud, "CoinCounter", AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd"),
                new Color(0.30f, 0.20f, 0.13f, 0.9f), new Vector2(1f, 1f), new Vector2(-30f, -30f), new Vector2(240f, 64f));
            var label = AddStretchedText(panel.transform, "Label", 30, font, cream, TextAnchor.MiddleCenter);

            var delta = AddStretchedText(panel.transform, "Delta", 26, font, cream, TextAnchor.UpperCenter);
            var deltaRect = (RectTransform)delta.transform;
            deltaRect.anchorMin = new Vector2(0f, 0f);
            deltaRect.anchorMax = new Vector2(1f, 0f);
            deltaRect.offsetMin = new Vector2(0f, -40f);
            deltaRect.offsetMax = new Vector2(0f, -6f);

            var counter = panel.AddComponent<CoinCounterUI>();
            var so = new SerializedObject(counter);
            so.FindProperty("wallet").objectReferenceValue = wallet;
            so.FindProperty("label").objectReferenceValue = label;
            so.FindProperty("deltaLabel").objectReferenceValue = delta;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Nivel de artista bajo el contador de monedas (deja libre el hueco del "+30"): texto y barra fina.</summary>
        static void BuildLevelCounter(Transform hud, ArtistLevel artistLevel)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var cream = new Color(1f, 0.95f, 0.82f);
            var sprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");
            var panel = CreatePanel(hud, "LevelCounter", sprite, new Color(0.30f, 0.20f, 0.13f, 0.9f),
                new Vector2(1f, 1f), new Vector2(-30f, -145f), new Vector2(240f, 50f));
            var label = AddStretchedText(panel.transform, "Label", 22, font, cream, TextAnchor.UpperCenter);
            ((RectTransform)label.transform).offsetMin = new Vector2(0f, 14f);

            var track = CreatePanel(panel.transform, "BarTrack", sprite, new Color(0.16f, 0.11f, 0.08f, 1f),
                new Vector2(0.5f, 0f), new Vector2(0f, 8f), new Vector2(210f, 8f));
            var fill = CreatePanel(track.transform, "BarFill", sprite, new Color(0.55f, 0.85f, 0.4f),
                new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(210f, 8f)).GetComponent<Image>();
            fill.type = Image.Type.Filled;
            fill.fillMethod = Image.FillMethod.Horizontal;

            var counter = panel.AddComponent<LevelCounterUI>();
            var so = new SerializedObject(counter);
            so.FindProperty("level").objectReferenceValue = artistLevel;
            so.FindProperty("label").objectReferenceValue = label;
            so.FindProperty("fill").objectReferenceValue = fill;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Objetivo del tutorial arriba a la izquierda: cabecera "Next" y el texto del paso actual.</summary>
        static void BuildTutorialObjectives(Transform hud, GameObject player, PaintModeController paintMode, PaintingPlacer placer)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var cream = new Color(1f, 0.95f, 0.82f);
            var panel = CreatePanel(hud, "TutorialObjective", AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd"),
                new Color(0.16f, 0.11f, 0.08f, 0.75f), new Vector2(0f, 1f), new Vector2(30f, -30f), new Vector2(380f, 90f));
            var header = AddStretchedText(panel.transform, "Header", 16, font, new Color(0.85f, 0.7f, 0.4f), TextAnchor.UpperLeft);
            ((RectTransform)header.transform).offsetMin = new Vector2(12f, 0f);
            ((RectTransform)header.transform).offsetMax = new Vector2(-12f, -6f);
            header.text = "Next";
            var label = AddStretchedText(panel.transform, "Label", 22, font, cream, TextAnchor.MiddleLeft);
            ((RectTransform)label.transform).offsetMin = new Vector2(12f, 4f);
            ((RectTransform)label.transform).offsetMax = new Vector2(-12f, -26f);

            var tutorial = panel.AddComponent<TutorialObjectives>();
            var so = new SerializedObject(tutorial);
            so.FindProperty("finisher").objectReferenceValue = paintMode.GetComponent<PaintingFinisher>();
            so.FindProperty("paintMode").objectReferenceValue = paintMode;
            so.FindProperty("group").objectReferenceValue = panel.AddComponent<CanvasGroup>();
            so.FindProperty("placer").objectReferenceValue = placer;
            so.FindProperty("inventory").objectReferenceValue = player.GetComponent<PlayerInventory>();
            so.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
            so.FindProperty("panel").objectReferenceValue = panel;
            so.FindProperty("label").objectReferenceValue = label;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Estación, día y hora, bajo el nivel de artista.</summary>
        static void BuildSeasonCounter(Transform hud, SeasonClock clock)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var cream = new Color(1f, 0.95f, 0.82f);
            var sprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");
            var panel = CreatePanel(hud, "SeasonCounter", sprite, new Color(0.30f, 0.20f, 0.13f, 0.9f),
                new Vector2(1f, 1f), new Vector2(-30f, -205f), new Vector2(330f, 40f));
            var label = AddStretchedText(panel.transform, "Label", 22, font, cream, TextAnchor.MiddleCenter);

            var counter = panel.AddComponent<SeasonCounterUI>();
            var so = new SerializedObject(counter);
            so.FindProperty("clock").objectReferenceValue = clock;
            so.FindProperty("label").objectReferenceValue = label;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>
        /// Calendario (C / cruceta arriba): panel centrado con título y botones para hojear estaciones, cabecera de días de la
        /// semana, cuadrícula de 7 columnas (las celdas las clona CalendarUI en runtime) y una línea con el próximo evento.
        /// </summary>
        static CalendarUI BuildCalendarUI(Transform hud, GameObject player, GameObject rig, SeasonClock clock,
            PaintModeController paintMode, PaintingPlacer placer)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var cream = new Color(1f, 0.95f, 0.82f);
            var brown = new Color(0.25f, 0.17f, 0.1f);
            var uiSprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");
            var resources = new DefaultControls.Resources
            {
                standard = uiSprite,
                background = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Background.psd"),
                knob = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Knob.psd")
            };

            var root = new GameObject("CalendarUI", typeof(RectTransform));
            root.transform.SetParent(hud, false);
            var rootRect = (RectTransform)root.transform;
            rootRect.anchorMin = Vector2.zero;
            rootRect.anchorMax = Vector2.one;
            rootRect.offsetMin = rootRect.offsetMax = Vector2.zero;

            var panel = CreatePanel(root.transform, "Panel", uiSprite, new Color(0.30f, 0.20f, 0.13f, 0.95f),
                new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(940f, 620f));
            panel.GetComponent<Image>().raycastTarget = true; // los clics no atraviesan el panel
            var title = AddStretchedText(panel.transform, "Title", 32, font, cream, TextAnchor.UpperCenter);
            ((RectTransform)title.transform).offsetMax = new Vector2(0f, -16f);

            // Botones para hojear las 4 estaciones, a los lados del título.
            var prev = CreateButton(resources, panel.transform, "Prev", "<", 28, font);
            var next = CreateButton(resources, panel.transform, "Next", ">", 28, font);
            foreach (var (button, x) in new[] { (prev, -300f), (next, 300f) })
            {
                var rect = (RectTransform)button.transform;
                rect.anchorMin = rect.anchorMax = rect.pivot = new Vector2(0.5f, 1f);
                rect.anchoredPosition = new Vector2(x, -12f);
                rect.sizeDelta = new Vector2(70f, 50f);
            }

            // Cabecera con los días de la semana (7 x 118 px + 6 x 6 px de separación = 862 px).
            var header = new GameObject("Weekdays", typeof(RectTransform), typeof(HorizontalLayoutGroup));
            header.transform.SetParent(panel.transform, false);
            var headerRect = (RectTransform)header.transform;
            headerRect.anchorMin = headerRect.anchorMax = headerRect.pivot = new Vector2(0.5f, 1f);
            headerRect.anchoredPosition = new Vector2(0f, -76f);
            headerRect.sizeDelta = new Vector2(862f, 28f);
            var headerLayout = header.GetComponent<HorizontalLayoutGroup>();
            headerLayout.spacing = 6f;
            headerLayout.childControlWidth = headerLayout.childControlHeight = true;
            headerLayout.childForceExpandWidth = headerLayout.childForceExpandHeight = true;
            foreach (var day in new[] { "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun" })
                AddLabel(header.transform, day, day, 20, 28f, font, cream);

            // Cuadrícula de días: 7 columnas.
            var grid = new GameObject("Grid", typeof(RectTransform), typeof(GridLayoutGroup));
            grid.transform.SetParent(panel.transform, false);
            var gridRect = (RectTransform)grid.transform;
            gridRect.anchorMin = gridRect.anchorMax = gridRect.pivot = new Vector2(0.5f, 1f);
            gridRect.anchoredPosition = new Vector2(0f, -110f);
            gridRect.sizeDelta = new Vector2(862f, 370f);
            var gridLayout = grid.GetComponent<GridLayoutGroup>();
            gridLayout.cellSize = new Vector2(118f, 88f);
            gridLayout.spacing = new Vector2(6f, 6f);
            gridLayout.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
            gridLayout.constraintCount = 7;

            // Celda plantilla: número del día arriba a la izquierda y hasta 2 eventos abajo; el borde marca hoy.
            var cell = new GameObject("CellTemplate", typeof(RectTransform), typeof(Image), typeof(Outline));
            cell.transform.SetParent(grid.transform, false);
            var cellImage = cell.GetComponent<Image>();
            cellImage.sprite = uiSprite;
            cellImage.type = Image.Type.Sliced;
            cellImage.color = new Color(0.93f, 0.88f, 0.78f);
            cellImage.raycastTarget = false;
            var outline = cell.GetComponent<Outline>();
            outline.effectDistance = new Vector2(3f, -3f);
            outline.enabled = false;
            var number = AddStretchedText(cell.transform, "Number", 22, font, brown, TextAnchor.UpperLeft);
            number.fontStyle = FontStyle.Bold;
            ((RectTransform)number.transform).offsetMin = new Vector2(8f, 0f);
            ((RectTransform)number.transform).offsetMax = new Vector2(0f, -4f);
            var events = AddStretchedText(cell.transform, "Events", 12, font, brown, TextAnchor.LowerCenter);
            ((RectTransform)events.transform).offsetMin = new Vector2(3f, 3f);
            ((RectTransform)events.transform).offsetMax = new Vector2(-3f, -26f);
            cell.SetActive(false);

            var footer = AddStretchedText(panel.transform, "Footer", 22, font, cream, TextAnchor.LowerCenter);
            ((RectTransform)footer.transform).offsetMin = new Vector2(0f, 90f);

            var close = CreateButton(resources, panel.transform, "Close", "Close", 24, font);
            var closeRect = (RectTransform)close.transform;
            closeRect.anchorMin = closeRect.anchorMax = closeRect.pivot = new Vector2(0.5f, 0f);
            closeRect.anchoredPosition = new Vector2(0f, 20f);
            closeRect.sizeDelta = new Vector2(200f, 56f);

            var calendarUi = root.AddComponent<CalendarUI>();
            var so = new SerializedObject(calendarUi);
            SetModalBaseRefs(so, panel, close.GetComponent<Button>(), player, rig);
            so.FindProperty("clock").objectReferenceValue = clock;
            so.FindProperty("toggleAction").objectReferenceValue = GetAction("Player/Calendar");
            so.FindProperty("paintMode").objectReferenceValue = paintMode;
            so.FindProperty("placer").objectReferenceValue = placer;
            so.FindProperty("titleLabel").objectReferenceValue = title;
            so.FindProperty("footerLabel").objectReferenceValue = footer;
            so.FindProperty("prevButton").objectReferenceValue = prev.GetComponent<Button>();
            so.FindProperty("nextButton").objectReferenceValue = next.GetComponent<Button>();
            so.FindProperty("cellContainer").objectReferenceValue = gridRect;
            so.FindProperty("cellTemplate").objectReferenceValue = cell;
            so.ApplyModifiedPropertiesWithoutUndo();
            return calendarUi;
        }

        /// <summary>
        /// Calendario de papel en la pared del fondo del estudio (cara visible hacia -Z), con la fecha de hoy escrita.
        /// Como el tablón de la galería: +Z local hacia la pared y trigger que sale hacia la sala.
        /// </summary>
        static void BuildWallCalendar(Transform environment, CalendarUI calendarUi, SeasonClock clock)
        {
            var paperMat = GetOrCreateMaterial("M_WallCalendar_Paper", new Color(0.95f, 0.91f, 0.80f));
            var stripMat = GetOrCreateMaterial("M_Accent_Terracotta", new Color(0.80f, 0.45f, 0.30f));

            var wallCalendar = new GameObject("WallCalendar");
            wallCalendar.transform.SetParent(environment);
            wallCalendar.transform.localPosition = new Vector3(5.2f, 1.6f, 5.87f);
            wallCalendar.transform.localRotation = Quaternion.identity;

            var box = wallCalendar.AddComponent<BoxCollider>();
            box.isTrigger = true;
            box.center = new Vector3(0f, 0f, -0.3f);
            box.size = new Vector3(1f, 1f, 0.6f);

            CreatePart(PrimitiveType.Cube, "Paper", wallCalendar.transform, Vector3.zero, new Vector3(0.6f, 0.8f, 0.04f), paperMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Header", wallCalendar.transform, new Vector3(0f, 0.33f, -0.03f), new Vector3(0.6f, 0.14f, 0.02f), stripMat, Quaternion.identity);

            // Canvas en el mundo: 1 unidad de UI = 1 mm.
            var canvasGo = new GameObject("Text", typeof(RectTransform), typeof(Canvas));
            canvasGo.transform.SetParent(wallCalendar.transform, false);
            canvasGo.transform.localPosition = new Vector3(0f, -0.08f, -0.045f);
            canvasGo.transform.localScale = Vector3.one * 0.001f;
            ((RectTransform)canvasGo.transform).sizeDelta = new Vector2(520f, 440f);
            canvasGo.GetComponent<Canvas>().renderMode = RenderMode.WorldSpace;

            var textGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
            textGo.transform.SetParent(canvasGo.transform, false);
            var textRect = (RectTransform)textGo.transform;
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.offsetMin = textRect.offsetMax = Vector2.zero;
            var label = textGo.GetComponent<Text>();
            label.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            label.alignment = TextAnchor.MiddleCenter;
            label.color = new Color(0.2f, 0.12f, 0.06f);
            label.resizeTextForBestFit = true;
            label.resizeTextMinSize = 20;
            label.resizeTextMaxSize = 160;
            label.raycastTarget = false;

            var so = new SerializedObject(wallCalendar.AddComponent<WallCalendar>());
            so.FindProperty("calendarUI").objectReferenceValue = calendarUi;
            so.FindProperty("clock").objectReferenceValue = clock;
            so.FindProperty("label").objectReferenceValue = label;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Fundido a negro entre días con "Spring 4" en el centro; va el último en el HUD para tapar todo.</summary>
        static void BuildDayFade(Transform hud, SeasonClock clock)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var root = new GameObject("DayFade", typeof(RectTransform), typeof(Image), typeof(CanvasGroup));
            root.transform.SetParent(hud, false);
            var rect = (RectTransform)root.transform;
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.offsetMin = rect.offsetMax = Vector2.zero;
            var image = root.GetComponent<Image>();
            image.color = Color.black;
            image.raycastTarget = false;
            var group = root.GetComponent<CanvasGroup>();
            group.alpha = 0f;
            group.blocksRaycasts = false;
            group.interactable = false;

            var label = AddStretchedText(root.transform, "Label", 56, font, new Color(1f, 0.95f, 0.82f), TextAnchor.MiddleCenter);

            var so = new SerializedObject(root.AddComponent<DayFadeUI>());
            so.FindProperty("clock").objectReferenceValue = clock;
            so.FindProperty("group").objectReferenceValue = group;
            so.FindProperty("label").objectReferenceValue = label;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static void SetMaterials(SerializedProperty array, params Material[] materials)
        {
            array.arraySize = materials.Length;
            for (int i = 0; i < materials.Length; i++)
                array.GetArrayElementAtIndex(i).objectReferenceValue = materials[i];
        }

        /// <summary>Caja de venta placeholder junto a la pared izquierda.</summary>
        static void BuildSellCrate(Transform parent, Vector3 position)
        {
            var crateMat = GetOrCreateMaterial("M_SellCrate_Wood", new Color(0.62f, 0.45f, 0.26f));
            var crate = new GameObject("SellCrate");
            crate.transform.SetParent(parent);
            crate.transform.localPosition = position;
            var box = crate.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, 0.3f, 0f);
            box.size = new Vector3(0.9f, 0.6f, 0.7f);

            CreatePart(PrimitiveType.Cube, "Base", crate.transform, new Vector3(0f, 0.05f, 0f), new Vector3(0.9f, 0.1f, 0.7f), crateMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Side_Front", crate.transform, new Vector3(0f, 0.3f, -0.33f), new Vector3(0.9f, 0.5f, 0.04f), crateMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Side_Back", crate.transform, new Vector3(0f, 0.3f, 0.33f), new Vector3(0.9f, 0.5f, 0.04f), crateMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Side_Left", crate.transform, new Vector3(-0.43f, 0.3f, 0f), new Vector3(0.04f, 0.5f, 0.62f), crateMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Side_Right", crate.transform, new Vector3(0.43f, 0.3f, 0f), new Vector3(0.04f, 0.5f, 0.62f), crateMat, Quaternion.identity);
            crate.AddComponent<SellCrate>();
        }

        /// <summary>
        /// Pueblo greybox al sur del estudio y el jardín (x -12..18, z -26..-6): césped, camino desde
        /// el hueco del estudio, plaza con fuente, casas de fachada, árboles, bancos y farolas sin luz.
        /// Solo para caminar; lo sólido tiene collider y el resto son detalles sin collider.
        /// </summary>
        static Transform BuildTown()
        {
            var grassMat = GetOrCreateMaterial("M_Town_Grass", new Color(0.40f, 0.47f, 0.35f));
            var pathMat = GetOrCreateMaterial("M_Town_Path", new Color(0.80f, 0.72f, 0.58f));
            var plazaMat = GetOrCreateMaterial("M_Town_Plaza", new Color(0.70f, 0.64f, 0.56f));
            var waterMat = GetOrCreateMaterial("M_Town_Water", new Color(0.32f, 0.42f, 0.51f));
            var stoneMat = GetOrCreateMaterial("M_Mortar_Stone", new Color(0.62f, 0.6f, 0.56f));
            var woodMat = GetOrCreateMaterial("M_Easel_Wood", new Color(0.42f, 0.28f, 0.18f));
            var bushMat = GetOrCreateMaterial("M_Garden_Bush", new Color(0.24f, 0.45f, 0.22f));
            var lampMat = GetOrCreateMaterial("M_Town_Lamp", new Color(0.16f, 0.15f, 0.15f));
            var lanternMat = GetOrCreateMaterial("M_Town_Lantern", new Color(0.32f, 0.29f, 0.24f));

            var town = new GameObject("Town").transform;

            // Suelo (techo en y = 0); camino y plaza apenas por encima para evitar z-fighting.
            CreateBlock("Town_Ground", town, new Vector3(3f, -0.1f, -16f), new Vector3(30f, 0.2f, 20f), grassMat);
            CreateBlock("Town_Path", town, new Vector3(0f, -0.09f, -8.5f), new Vector3(3f, 0.2f, 5f), pathMat);
            CreateBlock("Town_Plaza", town, new Vector3(0f, -0.08f, -16f), new Vector3(10f, 0.2f, 10f), plazaMat);
            // HUECO RESERVADO (Fase 14B): puesto de mercado alrededor de (-3, 0, -13), unos 4 x 4 m. No colocar nada aquí.

            // Fuente: pila baja de piedra con collider, agua y columna central.
            var fountain = new GameObject("Fountain").transform;
            fountain.SetParent(town, false);
            fountain.localPosition = new Vector3(0f, 0f, -16f);
            var basin = TownPart(PrimitiveType.Cylinder, "Fountain_Basin", fountain, new Vector3(0f, 0.3f, 0f), new Vector3(2.6f, 0.3f, 2.6f), stoneMat, Quaternion.identity);
            var basinCol = basin.AddComponent<MeshCollider>();
            basinCol.sharedMesh = basin.GetComponent<MeshFilter>().sharedMesh;
            basinCol.convex = true;
            TownPart(PrimitiveType.Cylinder, "Fountain_Water", fountain, new Vector3(0f, 0.61f, 0f), new Vector3(2.2f, 0.02f, 2.2f), waterMat, Quaternion.identity);
            TownPart(PrimitiveType.Cylinder, "Fountain_Column", fountain, new Vector3(0f, 0.9f, 0f), new Vector3(0.4f, 0.9f, 0.4f), stoneMat, Quaternion.identity);
            TownPart(PrimitiveType.Cylinder, "Fountain_Bowl", fountain, new Vector3(0f, 1.75f, 0f), new Vector3(0.9f, 0.08f, 0.9f), stoneMat, Quaternion.identity);

            // Casas de fachada mirando a la plaza (yaw: la puerta mira hacia (sin yaw, cos yaw)).
            BuildHouse(town, "House_West_A", new Vector3(-9.5f, 0f, -13f), 90f, new Vector3(5f, 3.2f, 4f), 1.2f, 2);
            BuildHouse(town, "House_West_B", new Vector3(-9.5f, 0f, -19f), 90f, new Vector3(4.5f, 3.8f, 3.6f), 1.0f, 1);
            BuildHouse(town, "House_South", new Vector3(2f, 0f, -23.5f), 0f, new Vector3(5.5f, 3.4f, 4f), 1.3f, 2);
            BuildHouse(town, "House_East", new Vector3(10f, 0f, -16f), -90f, new Vector3(5f, 4.0f, 4.2f), 1.1f, 2);

            // Árboles: solo el tronco es sólido.
            BuildTownTree(town, "Tree_A", new Vector3(-4.2f, 0f, -8f), 1.0f, woodMat, bushMat);
            BuildTownTree(town, "Tree_B", new Vector3(5.0f, 0f, -8.5f), 1.2f, woodMat, bushMat);
            BuildTownTree(town, "Tree_C", new Vector3(13.5f, 0f, -9f), 0.9f, woodMat, bushMat);
            BuildTownTree(town, "Tree_D", new Vector3(14.5f, 0f, -22f), 1.1f, woodMat, bushMat);
            BuildTownTree(town, "Tree_E", new Vector3(8.0f, 0f, -23.5f), 0.95f, woodMat, bushMat);
            BuildTownTree(town, "Tree_F", new Vector3(-8.5f, 0f, -24f), 1.15f, woodMat, bushMat);

            // Bancos junto a la plaza, mirando a la fuente (el lado del puesto queda libre).
            BuildBench(town, "Bench_East", new Vector3(3.9f, 0f, -16f), 270f, woodMat);
            BuildBench(town, "Bench_South", new Vector3(0f, 0f, -19.3f), 0f, woodMat);
            BuildBench(town, "Bench_NorthEast", new Vector3(3.2f, 0f, -12.2f), 200f, woodMat);

            // Farolas: solo las de la plaza llevan luz real (rendimiento); todas encienden la bombilla al anochecer.
            foreach (var p in new[] { new Vector3(-2.3f, 0f, -8f), new Vector3(2.3f, 0f, -8f), new Vector3(4.6f, 0f, -20.6f), new Vector3(-4.6f, 0f, -20.6f) })
            {
                TownPart(PrimitiveType.Cylinder, "Lamp_Post", town, p + new Vector3(0f, 1.4f, 0f), new Vector3(0.1f, 1.4f, 0.1f), lampMat, Quaternion.identity);
                var lantern = TownPart(PrimitiveType.Cube, "Lamp_Lantern", town, p + new Vector3(0f, 3.0f, 0f), new Vector3(0.3f, 0.4f, 0.3f), lanternMat, Quaternion.identity);
                Light lanternLight = null;
                if (p.z < -15f)
                    lanternLight = CreateLanternLight(town, p + new Vector3(0f, 2.8f, 0f), 7f);
                AddNightLamp(lantern, lanternLight, 0f, 2.5f, lantern.GetComponent<Renderer>(), lanternMat.GetColor("_BaseColor"));
            }

            // Límites invisibles: oeste, este, sur y el tramo norte al oeste del estudio.
            CreateBoundary("Boundary_Town_West", town, new Vector3(-12f, 1.5f, -16f), new Vector3(0.2f, 3f, 20f));
            CreateBoundary("Boundary_Town_East", town, new Vector3(18f, 1.5f, -16f), new Vector3(0.2f, 3f, 20f));
            CreateBoundary("Boundary_Town_South", town, new Vector3(3f, 1.5f, -26f), new Vector3(30f, 3f, 0.2f));
            CreateBoundary("Boundary_Town_North_West", town, new Vector3(-9f, 1.5f, -6f), new Vector3(6f, 3f, 0.2f));
            return town;
        }

        /// <summary>Primitiva decorativa del pueblo: sin collider y marcada como estática.</summary>
        static GameObject TownPart(PrimitiveType type, string name, Transform parent, Vector3 position, Vector3 scale, Material material, Quaternion rotation)
        {
            var go = CreatePart(type, name, parent, position, scale, material, rotation);
            go.isStatic = true;
            return go;
        }

        /// <summary>
        /// Casa de fachada (no se entra): cuerpo sólido, tejado a dos aguas, puerta y ventanas en la cara +Z local.
        /// <paramref name="size"/> es (ancho, alto, fondo); <paramref name="doorOffset"/> desplaza la puerta en x.
        /// </summary>
        static void BuildHouse(Transform parent, string name, Vector3 position, float yaw, Vector3 size, float doorOffset, int windows)
        {
            var wallMat = GetOrCreateMaterial("M_Town_Wall", new Color(0.88f, 0.80f, 0.69f));
            var roofMat = GetOrCreateMaterial("M_Town_Roof", new Color(0.66f, 0.37f, 0.28f));
            var doorMat = GetOrCreateMaterial("M_Town_Door", new Color(0.32f, 0.42f, 0.51f));
            var glassMat = GetOrCreateMaterial("M_Town_Window", new Color(0.35f, 0.40f, 0.45f));

            var house = new GameObject(name).transform;
            house.SetParent(parent, false);
            house.localPosition = position;
            house.localRotation = Quaternion.Euler(0f, yaw, 0f);

            float w = size.x, h = size.y, d = size.z;
            CreateBlock("Body", house, new Vector3(0f, h * 0.5f, 0f), size, wallMat);

            // Tejado a dos aguas: dos losas inclinadas sobre el eje x (la cumbrera corre a lo largo del ancho).
            const float angle = 35f;
            float rad = angle * Mathf.Deg2Rad;
            float slabLen = (d * 0.5f) / Mathf.Cos(rad) + 0.5f;
            float slabY = h + (d * 0.25f) * Mathf.Tan(rad) + 0.05f;
            for (int i = 0; i < 2; i++)
            {
                float side = i == 0 ? 1f : -1f; // +1 = lado de la fachada
                var slab = CreateBlock(i == 0 ? "Roof_Front" : "Roof_Back", house,
                    new Vector3(0f, slabY, side * d * 0.25f), new Vector3(w + 0.5f, 0.15f, slabLen), roofMat);
                slab.transform.localRotation = Quaternion.Euler(side * angle, 0f, 0f);
                Object.DestroyImmediate(slab.GetComponent<Collider>()); // el tejado queda fuera de alcance
            }

            // Puerta y ventanas pegadas a la fachada, sin collider.
            float fz = d * 0.5f + 0.03f;
            TownPart(PrimitiveType.Cube, "Door", house, new Vector3(doorOffset, 1.0f, fz), new Vector3(1.0f, 2.0f, 0.1f), doorMat, Quaternion.identity);
            float winX = doorOffset > 0f ? -w * 0.28f : w * 0.28f;
            TownPart(PrimitiveType.Cube, "Window_A", house, new Vector3(winX, 1.7f, fz), new Vector3(0.9f, 0.9f, 0.1f), glassMat, Quaternion.identity);
            if (windows > 1)
                TownPart(PrimitiveType.Cube, "Window_B", house, new Vector3(doorOffset, h - 0.8f, fz), new Vector3(0.9f, 0.7f, 0.1f), glassMat, Quaternion.identity);
        }

        /// <summary>Árbol: tronco sólido (cápsula) y copa de dos esferas sin collider.</summary>
        static void BuildTownTree(Transform parent, string name, Vector3 position, float scale, Material trunkMat, Material leafMat)
        {
            var tree = new GameObject(name).transform;
            tree.SetParent(parent, false);
            tree.localPosition = position;
            var trunk = TownPart(PrimitiveType.Cylinder, "Trunk", tree, new Vector3(0f, 1.1f * scale, 0f), new Vector3(0.35f * scale, 1.1f * scale, 0.35f * scale), trunkMat, Quaternion.identity);
            var col = trunk.AddComponent<CapsuleCollider>(); // radio 0,5 y alto 2 en local = el cilindro
            col.radius = 0.5f;
            col.height = 2f;
            TownPart(PrimitiveType.Sphere, "Crown_A", tree, new Vector3(0f, 2.8f * scale, 0f), Vector3.one * 2.4f * scale, leafMat, Quaternion.identity);
            TownPart(PrimitiveType.Sphere, "Crown_B", tree, new Vector3(0.5f * scale, 3.5f * scale, 0.2f * scale), Vector3.one * 1.6f * scale, leafMat, Quaternion.identity);
        }

        /// <summary>Banco: asiento sólido y respaldo; mira hacia +Z local.</summary>
        static void BuildBench(Transform parent, string name, Vector3 position, float yaw, Material woodMat)
        {
            var bench = new GameObject(name).transform;
            bench.SetParent(parent, false);
            bench.localPosition = position;
            bench.localRotation = Quaternion.Euler(0f, yaw, 0f);
            CreateBlock("Seat", bench, new Vector3(0f, 0.45f, 0f), new Vector3(1.6f, 0.1f, 0.5f), woodMat);
            TownPart(PrimitiveType.Cube, "Back", bench, new Vector3(0f, 0.8f, -0.22f), new Vector3(1.6f, 0.5f, 0.06f), woodMat, Quaternion.identity);
            TownPart(PrimitiveType.Cube, "Leg_L", bench, new Vector3(-0.7f, 0.2f, 0f), new Vector3(0.1f, 0.4f, 0.4f), woodMat, Quaternion.identity);
            TownPart(PrimitiveType.Cube, "Leg_R", bench, new Vector3(0.7f, 0.2f, 0f), new Vector3(0.1f, 0.4f, 0.4f), woodMat, Quaternion.identity);
        }

        /// <summary>
        /// Jardín al este del estudio (x de 6 a 18): césped al mismo nivel que el suelo, valla baja,
        /// límites invisibles y la puerta que lo abre al llegar al nivel pedido.
        /// </summary>
        static void BuildGarden(ArtistLevel artistLevel)
        {
            var grassMat = GetOrCreateMaterial("M_Grass", new Color(0.42f, 0.62f, 0.30f));
            var woodMat = GetOrCreateMaterial("M_Easel_Wood", new Color(0.42f, 0.28f, 0.18f));
            var bushMat = GetOrCreateMaterial("M_Garden_Bush", new Color(0.24f, 0.45f, 0.22f));
            var stoneMat = GetOrCreateMaterial("M_Mortar_Stone", new Color(0.62f, 0.6f, 0.56f));

            var garden = new GameObject("Garden").transform;
            CreateBlock("Lawn", garden, new Vector3(12f, -0.1f, 0f), new Vector3(12f, 0.2f, 12f), grassMat);

            // La valla es decorativa; quien frena al jugador son los límites invisibles.
            BuildFenceLine(garden, "Fence_South", new Vector3(6f, 0f, -6f), new Vector3(18f, 0f, -6f), woodMat);
            BuildFenceLine(garden, "Fence_East", new Vector3(18f, 0f, -6f), new Vector3(18f, 0f, 6f), woodMat);
            BuildFenceLine(garden, "Fence_North", new Vector3(18f, 0f, 6f), new Vector3(6f, 0f, 6f), woodMat);
            CreateBoundary("Boundary_South", garden, new Vector3(12f, 1.5f, -6f), new Vector3(12f, 3f, 0.2f));
            CreateBoundary("Boundary_East", garden, new Vector3(18f, 1.5f, 0f), new Vector3(0.2f, 3f, 12f));
            CreateBoundary("Boundary_North", garden, new Vector3(12f, 1.5f, 6f), new Vector3(12f, 3f, 0.2f));

            // Detalles sueltos, sin collider para no estorbar al colocar pinturas.
            CreatePart(PrimitiveType.Sphere, "Bush_A", garden, new Vector3(16.8f, 0.4f, 4.8f), new Vector3(1.3f, 0.9f, 1.3f), bushMat, Quaternion.identity);
            CreatePart(PrimitiveType.Sphere, "Bush_B", garden, new Vector3(16.9f, 0.3f, -4.6f), new Vector3(1f, 0.7f, 1f), bushMat, Quaternion.identity);
            CreatePart(PrimitiveType.Sphere, "Stone_A", garden, new Vector3(8.2f, 0.1f, 4.9f), new Vector3(0.5f, 0.3f, 0.4f), stoneMat, Quaternion.Euler(0f, 30f, 0f));
            CreatePart(PrimitiveType.Sphere, "Stone_B", garden, new Vector3(8.6f, 0.08f, -4.7f), new Vector3(0.4f, 0.25f, 0.35f), stoneMat, Quaternion.Euler(0f, 70f, 0f));

            BuildGardenGate(garden, artistLevel, woodMat);
            BuildLantern(garden, "Lantern_Garden_A", new Vector3(7.4f, 0f, -5.2f));
            BuildLantern(garden, "Lantern_Garden_B", new Vector3(16.6f, 0f, 0.5f));
        }

        /// <summary>Valla baja entre dos puntos: postes cada ~2 m y dos travesaños, todo sin collider.</summary>
        static void BuildFenceLine(Transform parent, string name, Vector3 from, Vector3 to, Material material)
        {
            var line = new GameObject(name).transform;
            line.SetParent(parent, false);
            var direction = to - from;
            var rotation = Quaternion.LookRotation(direction);
            foreach (float height in new[] { 0.35f, 0.7f })
                CreatePart(PrimitiveType.Cube, "Rail", line, (from + to) / 2f + Vector3.up * height,
                    new Vector3(0.06f, 0.08f, direction.magnitude), material, rotation);

            int segments = Mathf.RoundToInt(direction.magnitude / 2f);
            for (int i = 0; i <= segments; i++)
                CreatePart(PrimitiveType.Cube, "Post", line, Vector3.Lerp(from, to, i / (float)segments) + Vector3.up * 0.4f,
                    new Vector3(0.12f, 0.8f, 0.12f), material, Quaternion.identity);
        }

        /// <summary>Puerta en el hueco de x = 6: dos postes, un collider que cierra el paso y una hoja con bisagra en z = -1.</summary>
        static void BuildGardenGate(Transform parent, ArtistLevel artistLevel, Material material)
        {
            var gate = new GameObject("GardenGate");
            gate.transform.SetParent(parent, false);
            gate.transform.position = new Vector3(6f, 0f, 0f);

            // Capa "Ignore Raycast" como los límites: la cámara no se choca con la puerta.
            var blocker = new GameObject("Blocker") { layer = 2 };
            blocker.transform.SetParent(gate.transform, false);
            blocker.transform.localPosition = new Vector3(0f, 1.5f, 0f);
            var blockerBox = blocker.AddComponent<BoxCollider>();
            blockerBox.size = new Vector3(0.2f, 3f, 2f);

            foreach (float z in new[] { -1f, 1f })
                CreatePart(PrimitiveType.Cube, "Post", gate.transform, new Vector3(0f, 0.55f, z), new Vector3(0.18f, 1.1f, 0.18f), material, Quaternion.identity);

            var hinge = new GameObject("Hinge").transform;
            hinge.SetParent(gate.transform, false);
            hinge.localPosition = new Vector3(0f, 0f, -1f);
            foreach (float height in new[] { 0.3f, 0.6f, 0.9f })
                CreatePart(PrimitiveType.Cube, "Rail", hinge, new Vector3(0f, height, 0.95f), new Vector3(0.06f, 0.1f, 1.8f), material, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Brace", hinge, new Vector3(0f, 0.6f, 0.95f), new Vector3(0.06f, 0.1f, 1.9f), material, Quaternion.Euler(-25f, 0f, 0f));

            var component = gate.AddComponent<GardenGate>();
            var so = new SerializedObject(component);
            so.FindProperty("artistLevel").objectReferenceValue = artistLevel;
            so.FindProperty("blocker").objectReferenceValue = blockerBox;
            so.FindProperty("hinge").objectReferenceValue = hinge;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Los tipos de lienzo (assets en Data/Canvases): el primero es el estándar, con el que empieza el jugador.</summary>
        static CanvasType[] GetOrCreateCanvasTypes()
        {
            if (!AssetDatabase.IsValidFolder($"{Root}/Data/Canvases"))
                AssetDatabase.CreateFolder($"{Root}/Data", "Canvases");

            return new[]
            {
                GetOrCreateCanvasType("standard", "Standard canvas", "A plain canvas for the easel.", 1, 1f, 1f),
                GetOrCreateCanvasType("large", "Large canvas", "A big canvas: twice the harvest, twice the paint.", 2, 2f, 1.4f),
                GetOrCreateCanvasType("linen", "Linen canvas", "A forgiving linen weave: a little easier to reach a better quality.", 1, 1f, 1f, 0.05f),
                GetOrCreateCanvasType("gilded", "Gilded canvas", "Gold leaf edges: the art dealer pays double, but it takes more paint.", 1, 1.5f, 1f, 0f, 2f),
            };
        }

        static CanvasType GetOrCreateCanvasType(string id, string displayName, string description,
            int harvestMultiplier, float pigmentMultiplier, float plotScale, float scoreBonus = 0f, float sellMultiplier = 1f)
        {
            var path = $"{Root}/Data/Canvases/Canvas_{id}.asset";
            var canvasType = AssetDatabase.LoadAssetAtPath<CanvasType>(path);
            if (canvasType == null)
            {
                canvasType = ScriptableObject.CreateInstance<CanvasType>();
                AssetDatabase.CreateAsset(canvasType, path);
            }
            canvasType.EditorSetup(id, displayName, description, harvestMultiplier, pigmentMultiplier, plotScale, scoreBonus, sellMultiplier);
            EditorUtility.SetDirty(canvasType);
            return canvasType;
        }

        static CanvasOffer GetOrCreateCanvasOffer(string path, CanvasType canvasType, int price)
        {
            var offer = AssetDatabase.LoadAssetAtPath<CanvasOffer>(path);
            if (offer == null)
            {
                offer = ScriptableObject.CreateInstance<CanvasOffer>();
                AssetDatabase.CreateAsset(offer, path);
            }
            offer.EditorSetupOffer(canvasType.DisplayName, canvasType.Description, price, null);
            offer.EditorSetCanvasType(canvasType);
            EditorUtility.SetDirty(offer);
            return offer;
        }

        static CanvasUpgradeOffer GetOrCreateFineCanvasOffer(string path)
        {
            var offer = AssetDatabase.LoadAssetAtPath<CanvasUpgradeOffer>(path);
            if (offer == null)
            {
                offer = ScriptableObject.CreateInstance<CanvasUpgradeOffer>();
                AssetDatabase.CreateAsset(offer, path);
            }
            offer.EditorSetupOffer("Fine canvas weave", "Your easel canvases get a finer weave: paint with more detail.", 60, null);
            offer.EditorSetResolution(new Vector2Int(960, 768));
            EditorUtility.SetDirty(offer);
            return offer;
        }

        /// <summary>Ofertas de la tienda (assets en Data/Shop).</summary>
        static ShopOffer[] GetOrCreateShopOffers()
        {
            if (!AssetDatabase.IsValidFolder($"{Root}/Data/Shop"))
                AssetDatabase.CreateFolder($"{Root}/Data", "Shop");

            var canvasTypes = GetOrCreateCanvasTypes();
            var offers = new System.Collections.Generic.List<ShopOffer>
            {
                // La del lienzo estándar conserva el nombre de archivo original.
                GetOrCreateCanvasOffer($"{Root}/Data/Shop/Offer_Canvas.asset", canvasTypes[0], 5),
                GetOrCreateCanvasOffer($"{Root}/Data/Shop/Offer_Canvas_large.asset", canvasTypes[1], 15),
                GetOrCreateCanvasOffer($"{Root}/Data/Shop/Offer_Canvas_linen.asset", canvasTypes[2], 10),
                GetOrCreateCanvasOffer($"{Root}/Data/Shop/Offer_Canvas_gilded.asset", canvasTypes[3], 25),
            };
            foreach (var pigment in GetOrCreatePalette().Skip(StartingPigments))
            {
                var path = $"{Root}/Data/Shop/Offer_Pigment_{pigment.Id}.asset";
                var offer = AssetDatabase.LoadAssetAtPath<PigmentOffer>(path);
                if (offer == null)
                {
                    offer = ScriptableObject.CreateInstance<PigmentOffer>();
                    AssetDatabase.CreateAsset(offer, path);
                }
                offer.EditorSetupOffer(pigment.DisplayName, "A new color for your palette (+30).", 15, null);
                offer.EditorSetPigment(pigment);
                EditorUtility.SetDirty(offer);
                offers.Add(offer);
            }
            foreach (var pigment in GetOrCreatePalette())
            {
                var path = $"{Root}/Data/Shop/Offer_Refill_{pigment.Id}.asset";
                var refill = AssetDatabase.LoadAssetAtPath<RefillOffer>(path);
                if (refill == null)
                {
                    refill = ScriptableObject.CreateInstance<RefillOffer>();
                    AssetDatabase.CreateAsset(refill, path);
                }
                refill.EditorSetupOffer($"{pigment.DisplayName} jar", $"+30 {pigment.DisplayName.ToLowerInvariant()} pigment.", 8, null);
                refill.EditorSetPigment(pigment);
                EditorUtility.SetDirty(refill);
                offers.Add(refill);
            }

            foreach (var brush in GetOrCreateBrushes().Skip(StartingBrushes))
            {
                var path = $"{Root}/Data/Shop/Offer_Brush_{brush.Id}.asset";
                var offer = AssetDatabase.LoadAssetAtPath<BrushOffer>(path);
                if (offer == null)
                {
                    offer = ScriptableObject.CreateInstance<BrushOffer>();
                    AssetDatabase.CreateAsset(offer, path);
                }
                offer.EditorSetupOffer($"{brush.DisplayName} brush", BrushDescription(brush.Kind), 40, null);
                offer.EditorSetBrush(brush);
                EditorUtility.SetDirty(offer);
                offers.Add(offer);
            }

            foreach (var (tool, id, name, description) in new[]
            {
                (PaintTool.Eyedropper, "eyedropper", "Eyedropper", "Pick any color from your painting — even glaze mixes — and paint with it."),
                (PaintTool.Symmetry, "symmetry", "Symmetry", "Mirror every stroke across the middle of the canvas.")
            })
            {
                var path = $"{Root}/Data/Shop/Offer_Tool_{id}.asset";
                var offer = AssetDatabase.LoadAssetAtPath<ToolOffer>(path);
                if (offer == null)
                {
                    offer = ScriptableObject.CreateInstance<ToolOffer>();
                    AssetDatabase.CreateAsset(offer, path);
                }
                offer.EditorSetupOffer(name, description, 30, null);
                offer.EditorSetTool(tool);
                EditorUtility.SetDirty(offer);
                offers.Add(offer);
            }

            offers.Add(GetOrCreateFineCanvasOffer($"{Root}/Data/Shop/Offer_Upgrade_fine_canvas.asset"));

            foreach (var crop in GetOrCreateCrops().Skip(StartingCrops).SkipLast(HybridCrops))
            {
                var path = $"{Root}/Data/Shop/Offer_Sketch_{crop.Id}.asset";
                var offer = AssetDatabase.LoadAssetAtPath<SketchOffer>(path);
                if (offer == null)
                {
                    offer = ScriptableObject.CreateInstance<SketchOffer>();
                    AssetDatabase.CreateAsset(offer, path);
                }
                offer.EditorSetupOffer($"{crop.DisplayName} sketch", $"Adds the {crop.DisplayName.ToLowerInvariant()} to the crops you can paint.", 30, null);
                offer.EditorSetCrop(crop);
                EditorUtility.SetDirty(offer);
                offers.Add(offer);
            }
            foreach (var style in GetOrCreateStyles())
            {
                var path = $"{Root}/Data/Shop/Offer_Style_{style.Id}.asset";
                var offer = AssetDatabase.LoadAssetAtPath<StyleOffer>(path);
                if (offer == null)
                {
                    offer = ScriptableObject.CreateInstance<StyleOffer>();
                    AssetDatabase.CreateAsset(offer, path);
                }
                offer.EditorSetupOffer($"{style.DisplayName} style", style.Description, style.Kind == StyleKind.Swirl ? 70 : 50, null);
                offer.EditorSetStyle(style);
                EditorUtility.SetDirty(offer);
                offers.Add(offer);
            }
            foreach (var offer in offers)
            {
                offer.EditorSetRequiredLevel(RequiredLevel(offer.name));
                offer.EditorSetSeason(null);
                EditorUtility.SetDirty(offer);
            }

            // Pigmentos de temporada: como Violet, fuera de GetOrCreatePalette() (esa lista también genera ofertas de todo el año).
            // El color y su recarga solo se venden en su estación.
            foreach (var (season, id, name, color) in new[]
            {
                (Season.Spring, "blossom_pink", "Blossom Pink", new Color(0.93f, 0.62f, 0.70f)),
                (Season.Summer, "sky_blue", "Sky Blue", new Color(0.55f, 0.75f, 0.92f)),
                (Season.Autumn, "burnt_orange", "Burnt Orange", new Color(0.80f, 0.42f, 0.15f)),
                (Season.Winter, "frost_lilac", "Frost Lilac", new Color(0.76f, 0.72f, 0.88f))
            })
            {
                var pigment = GetOrCreatePigment(id, name, color);
                var path = $"{Root}/Data/Shop/Offer_Pigment_{id}.asset";
                var offer = AssetDatabase.LoadAssetAtPath<PigmentOffer>(path);
                if (offer == null)
                {
                    offer = ScriptableObject.CreateInstance<PigmentOffer>();
                    AssetDatabase.CreateAsset(offer, path);
                }
                offer.EditorSetupOffer(name, $"{season} only: a new color for your palette (+30).", 20, null);
                offer.EditorSetPigment(pigment);
                offer.EditorSetRequiredLevel(1);
                offer.EditorSetSeason(season);
                EditorUtility.SetDirty(offer);
                offers.Add(offer);

                var refillPath = $"{Root}/Data/Shop/Offer_Refill_{id}.asset";
                var refill = AssetDatabase.LoadAssetAtPath<RefillOffer>(refillPath);
                if (refill == null)
                {
                    refill = ScriptableObject.CreateInstance<RefillOffer>();
                    AssetDatabase.CreateAsset(refill, refillPath);
                }
                refill.EditorSetupOffer($"{name} jar", $"{season} only: +30 {name.ToLowerInvariant()} pigment.", 10, null);
                refill.EditorSetPigment(pigment);
                refill.EditorSetRequiredLevel(1);
                refill.EditorSetSeason(season);
                EditorUtility.SetDirty(refill);
                offers.Add(refill);
            }
            return offers.ToArray();
        }

        /// <summary>Nivel de artista que pide cada oferta (por nombre de asset); lo no listado es de nivel 1.</summary>
        static int RequiredLevel(string offerName) => offerName switch
        {
            "Offer_Pigment_carmine" or "Offer_Sketch_tomato" or "Offer_Brush_fill" or "Offer_Tool_symmetry" => 2,
            "Offer_Pigment_ultramarine" or "Offer_Pigment_titanium_white" or "Offer_Canvas_large" or "Offer_Brush_glaze"
                or "Offer_Tool_eyedropper" => 3,
            "Offer_Sketch_glowbell" or "Offer_Upgrade_fine_canvas" => 4,
            "Offer_Style_wash" or "Offer_Canvas_linen" => 5,
            "Offer_Style_swirl" or "Offer_Canvas_gilded" => 6,
            _ => 1
        };

        /// <summary>Piezas de un panel con filas (tienda, selector de cultivo).</summary>
        struct ListPanel
        {
            public GameObject Root;
            public GameObject Panel;
            public RectTransform Rows;
            public GameObject RowTemplate;
            public Button Close;
            public Text Message;
        }

        /// <summary>
        /// Panel centrado con título, filas (icono, nombre y botón "Buy"), un mensaje y botón Close.
        /// La fila plantilla la clona en runtime el ModalPanel correspondiente.
        /// </summary>
        static ListPanel BuildListPanel(Transform hud, string name, string titleText, Vector2 size)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var cream = new Color(1f, 0.95f, 0.82f);
            var uiSprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");
            var resources = new DefaultControls.Resources
            {
                standard = uiSprite,
                background = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Background.psd"),
                knob = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Knob.psd")
            };

            var root = new GameObject(name, typeof(RectTransform));
            root.transform.SetParent(hud, false);
            var rootRect = (RectTransform)root.transform;
            rootRect.anchorMin = Vector2.zero;
            rootRect.anchorMax = Vector2.one;
            rootRect.offsetMin = rootRect.offsetMax = Vector2.zero;

            var panel = CreatePanel(root.transform, "Panel", uiSprite, new Color(0.30f, 0.20f, 0.13f, 0.95f),
                new Vector2(0.5f, 0.5f), Vector2.zero, size);
            panel.GetComponent<Image>().raycastTarget = true; // los clics no atraviesan el panel
            var title = AddStretchedText(panel.transform, "Title", 32, font, cream, TextAnchor.UpperCenter);
            title.text = titleText;
            ((RectTransform)title.transform).offsetMax = new Vector2(0f, -16f);

            // Zona con scroll (rueda del ratón): las filas se apilan arriba y crecen hacia abajo.
            var scrollGo = new GameObject("Scroll", typeof(RectTransform), typeof(RectMask2D), typeof(ScrollRect));
            scrollGo.transform.SetParent(panel.transform, false);
            var scrollRect = (RectTransform)scrollGo.transform;
            scrollRect.anchorMin = Vector2.zero;
            scrollRect.anchorMax = Vector2.one;
            scrollRect.offsetMin = new Vector2(30f, 140f);
            scrollRect.offsetMax = new Vector2(-30f, -70f);

            var rowsGo = new GameObject("Rows", typeof(RectTransform), typeof(VerticalLayoutGroup), typeof(ContentSizeFitter));
            rowsGo.transform.SetParent(scrollGo.transform, false);
            var rowsRect = (RectTransform)rowsGo.transform;
            rowsRect.anchorMin = new Vector2(0f, 1f);
            rowsRect.anchorMax = Vector2.one;
            rowsRect.pivot = new Vector2(0.5f, 1f);
            rowsRect.offsetMin = rowsRect.offsetMax = Vector2.zero;
            var rowsLayout = rowsGo.GetComponent<VerticalLayoutGroup>();
            rowsLayout.spacing = 10f;
            rowsLayout.childControlWidth = rowsLayout.childControlHeight = true;
            rowsLayout.childForceExpandHeight = false;
            rowsGo.GetComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            var scroll = scrollGo.GetComponent<ScrollRect>();
            scroll.content = rowsRect;
            scroll.viewport = scrollRect;
            scroll.horizontal = false;
            scroll.movementType = ScrollRect.MovementType.Clamped;
            scroll.scrollSensitivity = 30f;

            // Fila plantilla: icono, nombre (+ descripción) y botón de acción.
            var row = new GameObject("RowTemplate", typeof(RectTransform), typeof(Image), typeof(LayoutElement));
            row.transform.SetParent(rowsGo.transform, false);
            row.GetComponent<LayoutElement>().preferredHeight = 80f;
            var rowImage = row.GetComponent<Image>();
            rowImage.sprite = uiSprite;
            rowImage.type = Image.Type.Sliced;
            rowImage.color = new Color(0.93f, 0.88f, 0.78f);

            var icon = new GameObject("Icon", typeof(RectTransform), typeof(RawImage));
            icon.transform.SetParent(row.transform, false);
            var iconRect = (RectTransform)icon.transform;
            iconRect.anchorMin = iconRect.anchorMax = iconRect.pivot = new Vector2(0f, 0.5f);
            iconRect.anchoredPosition = new Vector2(14f, 0f);
            iconRect.sizeDelta = new Vector2(80f, 64f);

            var nameText = AddStretchedText(row.transform, "Name", 24, font, new Color(0.25f, 0.17f, 0.1f), TextAnchor.MiddleLeft);
            var nameRect = (RectTransform)nameText.transform;
            nameRect.offsetMin = new Vector2(120f, 0f);
            nameRect.offsetMax = new Vector2(-180f, 0f);

            var buy = CreateButton(resources, row.transform, "Buy", "Buy", 24, font);
            buy.GetComponent<Image>().color = new Color(0.55f, 0.75f, 0.45f);
            var buyRect = (RectTransform)buy.transform;
            buyRect.anchorMin = buyRect.anchorMax = buyRect.pivot = new Vector2(1f, 0.5f);
            buyRect.anchoredPosition = new Vector2(-16f, 0f);
            buyRect.sizeDelta = new Vector2(150f, 56f);

            var message = AddStretchedText(panel.transform, "Message", 22, font, cream, TextAnchor.LowerCenter);
            ((RectTransform)message.transform).offsetMin = new Vector2(0f, 90f);

            var close = CreateButton(resources, panel.transform, "Close", "Close", 24, font);
            var closeRect = (RectTransform)close.transform;
            closeRect.anchorMin = closeRect.anchorMax = closeRect.pivot = new Vector2(0.5f, 0f);
            closeRect.anchoredPosition = new Vector2(0f, 20f);
            closeRect.sizeDelta = new Vector2(200f, 56f);

            return new ListPanel
            {
                Root = root, Panel = panel, Rows = rowsRect, RowTemplate = row,
                Close = close.GetComponent<Button>(), Message = message
            };
        }

        /// <summary>Referencias comunes de un ModalPanel (cursor, cámara, interacción y cierre).</summary>
        static void SetModalPanelRefs(SerializedObject so, ListPanel ui, GameObject player, GameObject rig)
        {
            SetModalBaseRefs(so, ui.Panel, ui.Close, player, rig);
            so.FindProperty("rowContainer").objectReferenceValue = ui.Rows;
            so.FindProperty("rowTemplate").objectReferenceValue = ui.RowTemplate;
        }

        /// <summary>Campos de ModalPanel que comparten todos los paneles, tengan o no filas.</summary>
        static void SetModalBaseRefs(SerializedObject so, GameObject panel, Button closeButton, GameObject player, GameObject rig)
        {
            so.FindProperty("interactor").objectReferenceValue = player.GetComponent<PlayerInteractor>();
            so.FindProperty("cursorLock").objectReferenceValue = rig.GetComponent<CursorLock>();
            so.FindProperty("cameraMode").objectReferenceValue = rig.GetComponent<CameraModeController>();
            so.FindProperty("exitAction").objectReferenceValue = GetAction("Paint/Exit");
            so.FindProperty("panel").objectReferenceValue = panel;
            so.FindProperty("closeButton").objectReferenceValue = closeButton;
        }

        /// <summary>Mortero sobre un tocón junto a la pared del fondo + panel para moler la cosecha.</summary>
        static void BuildMortar(Transform hud, Transform environment, GameObject player, GameObject rig, PaintBrushController brush)
        {
            var ui = BuildListPanel(hud, "MortarUI", "Mortar", new Vector2(760f, 640f));
            var mortar = ui.Root.AddComponent<MortarUI>();
            var so = new SerializedObject(mortar);
            SetModalPanelRefs(so, ui, player, rig);
            so.FindProperty("inventory").objectReferenceValue = player.GetComponent<PlayerInventory>();
            so.FindProperty("stock").objectReferenceValue = player.GetComponent<PigmentStock>();
            so.FindProperty("brush").objectReferenceValue = brush;
            so.FindProperty("messageLabel").objectReferenceValue = ui.Message;
            so.ApplyModifiedPropertiesWithoutUndo();

            var stumpMat = GetOrCreateMaterial("M_Easel_Wood", new Color(0.42f, 0.28f, 0.18f));
            var stoneMat = GetOrCreateMaterial("M_Mortar_Stone", new Color(0.62f, 0.6f, 0.56f));
            var station = new GameObject("Mortar");
            station.transform.SetParent(environment);
            station.transform.localPosition = new Vector3(-2.3f, 0f, 4.8f);
            var box = station.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, 0.4f, 0f);
            box.size = new Vector3(0.7f, 0.8f, 0.7f);

            CreatePart(PrimitiveType.Cylinder, "Stump", station.transform, new Vector3(0f, 0.3f, 0f), new Vector3(0.6f, 0.3f, 0.6f), stumpMat, Quaternion.identity);
            CreatePart(PrimitiveType.Sphere, "Bowl", station.transform, new Vector3(0f, 0.66f, 0f), new Vector3(0.36f, 0.2f, 0.36f), stoneMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cylinder, "Pestle", station.transform, new Vector3(0.08f, 0.8f, 0f), new Vector3(0.05f, 0.14f, 0.05f), stoneMat, Quaternion.Euler(0f, 0f, -25f));
            var stationSo = new SerializedObject(station.AddComponent<MortarStation>());
            stationSo.FindProperty("mortar").objectReferenceValue = mortar;
            stationSo.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>
        /// Galería detrás del estudio (x de -6 a 6, z de 6 a 14), sin techo: suelo, paredes y 6 marcos vacíos
        /// (2 por pared lateral y 2 al fondo) + el panel para colgar pinturas.
        /// </summary>
        static Transform BuildGallery(Transform hud, DialogueUI dialogueUi, CommissionUI commissionUi, GameObject player, GameObject rig, Material wallMat, PaintBrushController brush, SeasonClock seasonClock)
        {
            var floorMat = GetOrCreateMaterial("M_Gallery_Floor", new Color(0.74f, 0.68f, 0.60f));
            var woodMat = GetOrCreateMaterial("M_Gallery_Frame", new Color(0.25f, 0.17f, 0.11f));

            var ui = BuildListPanel(hud, "GalleryHangUI", "Hang a painting", new Vector2(760f, 640f));
            var hangUi = ui.Root.AddComponent<GalleryHangUI>();
            var so = new SerializedObject(hangUi);
            SetModalPanelRefs(so, ui, player, rig);
            so.FindProperty("inventory").objectReferenceValue = player.GetComponent<PlayerInventory>();
            so.FindProperty("messageLabel").objectReferenceValue = ui.Message;
            so.ApplyModifiedPropertiesWithoutUndo();

            var gallery = new GameObject("Gallery").transform;
            CreateBlock("Floor", gallery, new Vector3(0f, -0.1f, 10f), new Vector3(12f, 0.2f, 8f), floorMat);
            CreateBlock("Wall_Left", gallery, new Vector3(-6f, 1.5f, 10f), new Vector3(0.2f, 3f, 8f), wallMat);
            CreateBlock("Wall_Right", gallery, new Vector3(6f, 1.5f, 10f), new Vector3(0.2f, 3f, 8f), wallMat);
            CreateBlock("Wall_Back", gallery, new Vector3(0f, 1.5f, 14f), new Vector3(12.2f, 3f, 0.2f), wallMat);

            // Luz cálida suave para que la sala no quede a oscuras.
            foreach (float z in new[] { 8.5f, 11.5f })
            {
                var lightGo = new GameObject("Light");
                lightGo.transform.SetParent(gallery, false);
                lightGo.transform.localPosition = new Vector3(0f, 2.6f, z);
                var light = lightGo.AddComponent<Light>();
                light.type = LightType.Point;
                light.color = new Color(1f, 0.9f, 0.75f);
                light.range = 8f;
                light.intensity = 2f;
                AddNightLamp(lightGo, light, 0.8f, 2f, null, default); // de día, al 40 %
            }

            // Cada marco mira hacia dentro de la sala: su +Z local apunta a la pared.
            var inventory = player.GetComponent<PlayerInventory>();
            BuildGalleryFrame(gallery, "Frame_L1", new Vector3(-5.9f, 1.6f, 8.5f), Quaternion.Euler(0f, -90f, 0f), woodMat, hangUi, inventory);
            BuildGalleryFrame(gallery, "Frame_L2", new Vector3(-5.9f, 1.6f, 11.5f), Quaternion.Euler(0f, -90f, 0f), woodMat, hangUi, inventory);
            BuildGalleryFrame(gallery, "Frame_R1", new Vector3(5.9f, 1.6f, 8.5f), Quaternion.Euler(0f, 90f, 0f), woodMat, hangUi, inventory);
            BuildGalleryFrame(gallery, "Frame_R2", new Vector3(5.9f, 1.6f, 11.5f), Quaternion.Euler(0f, 90f, 0f), woodMat, hangUi, inventory);
            BuildGalleryFrame(gallery, "Frame_B1", new Vector3(-3.5f, 1.6f, 13.9f), Quaternion.identity, woodMat, hangUi, inventory);
            BuildGalleryFrame(gallery, "Frame_B2", new Vector3(3.5f, 1.6f, 13.9f), Quaternion.identity, woodMat, hangUi, inventory);
            BuildCollectionBoard(hud, gallery, player, rig, woodMat, brush);
            BuildNpc(gallery, dialogueUi, commissionUi, player, brush, seasonClock);
            return gallery;
        }

        /// <summary>Panel de diálogo compartido por todos los personajes.</summary>
        static DialogueUI BuildDialogueUI(Transform hud, GameObject player, GameObject rig)
        {
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var cream = new Color(1f, 0.95f, 0.82f);
            var uiSprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");
            var resources = new DefaultControls.Resources
            {
                standard = uiSprite,
                background = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Background.psd"),
                knob = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/Knob.psd")
            };

            // Panel de diálogo: nombre arriba a la izquierda, la línea en el centro, Next abajo a la derecha.
            var root = new GameObject("DialogueUI", typeof(RectTransform));
            root.transform.SetParent(hud, false);
            var rootRect = (RectTransform)root.transform;
            rootRect.anchorMin = Vector2.zero;
            rootRect.anchorMax = Vector2.one;
            rootRect.offsetMin = rootRect.offsetMax = Vector2.zero;

            var panel = CreatePanel(root.transform, "Panel", uiSprite, new Color(0.30f, 0.20f, 0.13f, 0.95f),
                new Vector2(0.5f, 0f), new Vector2(0f, 40f), new Vector2(900f, 220f));
            panel.GetComponent<Image>().raycastTarget = true; // los clics no atraviesan el panel

            var speaker = AddStretchedText(panel.transform, "Speaker", 30, font, new Color(1f, 0.85f, 0.45f), TextAnchor.UpperLeft);
            var speakerRect = (RectTransform)speaker.transform;
            speakerRect.offsetMin = new Vector2(30f, 0f);
            speakerRect.offsetMax = new Vector2(-200f, -16f);

            var line = AddStretchedText(panel.transform, "Line", 26, font, cream, TextAnchor.UpperLeft);
            var lineRect = (RectTransform)line.transform;
            lineRect.offsetMin = new Vector2(30f, 80f);
            lineRect.offsetMax = new Vector2(-30f, -60f);

            var next = CreateButton(resources, panel.transform, "Next", "Next", 24, font);
            next.GetComponent<Image>().color = new Color(0.55f, 0.75f, 0.45f);
            var nextRect = (RectTransform)next.transform;
            nextRect.anchorMin = nextRect.anchorMax = nextRect.pivot = new Vector2(1f, 0f);
            nextRect.anchoredPosition = new Vector2(-24f, 16f);
            nextRect.sizeDelta = new Vector2(160f, 52f);

            var close = CreateButton(resources, panel.transform, "Close", "Close", 20, font);
            var closeRect = (RectTransform)close.transform;
            closeRect.anchorMin = closeRect.anchorMax = closeRect.pivot = new Vector2(1f, 1f);
            closeRect.anchoredPosition = new Vector2(-16f, -14f);
            closeRect.sizeDelta = new Vector2(120f, 40f);

            var dialogueUi = root.AddComponent<DialogueUI>();
            var uiSo = new SerializedObject(dialogueUi);
            SetModalBaseRefs(uiSo, panel, close.GetComponent<Button>(), player, rig);
            uiSo.FindProperty("speakerLabel").objectReferenceValue = speaker;
            uiSo.FindProperty("lineLabel").objectReferenceValue = line;
            uiSo.FindProperty("nextButton").objectReferenceValue = next.GetComponent<Button>();
            uiSo.FindProperty("nextLabel").objectReferenceValue = next.GetComponentInChildren<Text>();
            uiSo.ApplyModifiedPropertiesWithoutUndo();

            return dialogueUi;
        }

        /// <summary>Panel de entrega de pinturas, compartido por Ottilie y el tablón de encargos.</summary>
        static CommissionUI BuildCommissionUI(Transform hud, GameObject player, GameObject rig)
        {
            var commissionList = BuildListPanel(hud, "CommissionUI", "Give a painting", new Vector2(760f, 640f));
            var commissionUi = commissionList.Root.AddComponent<CommissionUI>();
            var commissionSo = new SerializedObject(commissionUi);
            SetModalPanelRefs(commissionSo, commissionList, player, rig);
            commissionSo.FindProperty("inventory").objectReferenceValue = player.GetComponent<PlayerInventory>();
            commissionSo.FindProperty("messageLabel").objectReferenceValue = commissionList.Message;
            commissionSo.ApplyModifiedPropertiesWithoutUndo();
            return commissionUi;
        }

        /// <summary>Ottilie Vane, coleccionista excéntrica (figura de primitivas) en la galería.</summary>
        static void BuildNpc(Transform gallery, DialogueUI dialogueUi, CommissionUI commissionUi, GameObject player, PaintBrushController brush, SeasonClock seasonClock)
        {
            // Datos del personaje.
            if (!AssetDatabase.IsValidFolder($"{Root}/Data/Npcs"))
                AssetDatabase.CreateFolder($"{Root}/Data", "Npcs");
            var definitionPath = $"{Root}/Data/Npcs/Npc_OttilieVane.asset";
            var definition = AssetDatabase.LoadAssetAtPath<NpcDefinition>(definitionPath);
            if (definition == null)
            {
                definition = ScriptableObject.CreateInstance<NpcDefinition>();
                AssetDatabase.CreateAsset(definition, definitionPath);
            }
            // Violet solo se consigue como recompensa: no entra en GetOrCreatePalette() (esa lista también genera las ofertas de la tienda).
            var violet = GetOrCreatePigment("violet", "Violet", new Color(0.52f, 0.30f, 0.68f));
            var sunflower = GetOrCreateSunflowerCrop();
            var sunflowerCommission = GetOrCreateCommission("Commission_OttilieSunflower", sunflower, null, PaintingQuality.Good, new[]
            {
                "Now then, darling, I have a little something to ask of you.",
                "I would simply adore a sunflower painting for my collection. A proper one, mind: Good quality or better.",
                "Bring it to me when it is ready, and I shall be waiting with bated breath."
            }, new[]
            {
                "Oh, it is magnificent! Look at those petals, they practically hum. This will be the very first jewel of my collection.",
                "Mark my words, I shall have more requests for you soon. A collector's appetite is never satisfied!"
            }, 40, 30);
            var tomatoCommission = GetOrCreateCommission("Commission_OttilieTomato", GetOrCreateTomatoCrop(), null, PaintingQuality.Excellent, new[]
            {
                "Darling, you are back, and my appetite is wonderfully awake!",
                "This time I crave a tomato. Not a shy, pale thing: a bold, ripe, outrageously red one. Excellent quality, if you please.",
                "Paint it as though you could taste it, and bring it straight to me."
            }, new[]
            {
                "Splendid! I can practically smell the vine on it. Ripe, bold, and not a hint of shyness.",
                "You have a real gift, my dear. Take this with my gratitude!"
            }, 60, 40);
            var blueCommission = GetOrCreateCommission("Commission_OttilieBlueSunflower", sunflower, "blue", PaintingQuality.Good, new[]
            {
                "Come closer, darling, and keep your voice down. I have heard a rumour.",
                "They say there is a sunflower out there with petals as blue as a summer evening. A Blue Sunflower! I can think of nothing else.",
                "I suspect you would need some blue for those petals. Bring me one, Good quality or better, and I shall reward you handsomely."
            }, new[]
            {
                "A blue sunflower! The rumours were true, and I am positively giddy.",
                "Here, a colour you won't find in any shop. Treat it kindly, and paint something wonderful with it!"
            }, 80, 50, violet, 30);

            var swirlStyle = System.Array.Find(GetOrCreateStyles(), s => s.Kind == StyleKind.Swirl);
            var swirlCommission = GetOrCreateCommission("Commission_OttilieSwirlSunflower", sunflower, null, PaintingQuality.Good, new[]
            {
                "Darling, I have a new obsession: swirls! Great, rolling, dizzy brushstrokes that make the whole canvas feel alive.",
                "Paint me a sunflower in the Swirl style, Good quality or better. I want to feel the wind in those petals.",
                "No Swirl style yet? The shop sells it, darling. Go and treat yourself, then come straight back to me!"
            }, new[]
            {
                "Look at it move! Every stroke is a little whirlwind. I could stare at it for hours.",
                "You have a wild hand, darling, and I mean that as the highest of compliments."
            }, 100, 60, null, 0, swirlStyle);

            definition.EditorSetup("Ottilie Vane", new[]
            {
                "Oh! A new face among my favourite walls. I'm Ottilie Vane, and I collect colours the way other people collect teaspoons.",
                "Rare pigments make my heart flutter. And paintings that grow? Darling, I would cross three counties for one.",
                "Keep your brushes wet and your garden wilder than is sensible. The best colours always sprout where nobody planned them.",
                "I may have a request or two for you, once you have settled in. Do come and chat again soon!"
            }, new[] { sunflowerCommission, tomatoCommission, blueCommission, swirlCommission });
            definition.EditorSetSeasonLines(new[]
            {
                "Spring, darling! Everything is blushing pink and showing off. I approve.",
                "This summer light makes every colour shout. I adore a shouting colour.",
                "Autumn light suits the gallery, doesn't it? All those warm, tired golds.",
                "Winter, and the world has gone pale. All the more reason to paint something bright, darling."
            });
            EditorUtility.SetDirty(definition);

            // Figura de ~1,75 m: un único CapsuleCollider en la raíz (CreatePart quita los de las primitivas).
            var coatMat = GetOrCreateMaterial("M_Npc_Coat", new Color(0.30f, 0.12f, 0.30f));
            var skinMat = GetOrCreateMaterial("M_Npc_Skin", new Color(0.93f, 0.74f, 0.60f));
            var hatMat = GetOrCreateMaterial("M_Npc_Hat", new Color(0.85f, 0.70f, 0.30f));
            var scarfMat = GetOrCreateMaterial("M_Npc_Scarf", new Color(0.90f, 0.40f, 0.30f));

            var npc = new GameObject("Npc_OttilieVane");
            npc.transform.SetParent(gallery, false);
            npc.transform.SetPositionAndRotation(new Vector3(-3f, 0f, 10.5f), Quaternion.Euler(0f, 90f, 0f)); // mira al centro de la sala
            var capsule = npc.AddComponent<CapsuleCollider>();
            capsule.center = new Vector3(0f, 0.875f, 0f);
            capsule.radius = 0.3f;
            capsule.height = 1.75f;

            // El cuerpo cuelga de "Visual" (respira sin pelearse con el giro hacia el jugador, que mueve la raíz).
            var visual = new GameObject("Visual").transform;
            visual.SetParent(npc.transform, false);
            CreatePart(PrimitiveType.Capsule, "Coat", visual, new Vector3(0f, 0.6f, 0f), new Vector3(0.55f, 0.6f, 0.55f), coatMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cylinder, "Scarf", visual, new Vector3(0f, 1.27f, 0f), new Vector3(0.34f, 0.04f, 0.34f), scarfMat, Quaternion.identity);
            CreatePart(PrimitiveType.Sphere, "Head", visual, new Vector3(0f, 1.43f, 0f), Vector3.one * 0.26f, skinMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cylinder, "Hat_Brim", visual, new Vector3(0f, 1.55f, 0f), new Vector3(0.5f, 0.012f, 0.5f), hatMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cylinder, "Hat_Crown", visual, new Vector3(0f, 1.65f, 0f), new Vector3(0.2f, 0.1f, 0.2f), hatMat, Quaternion.identity);

            var component = npc.AddComponent<Npc>();
            var so = new SerializedObject(component);
            so.FindProperty("definition").objectReferenceValue = definition;
            so.FindProperty("dialogueUI").objectReferenceValue = dialogueUi;
            so.FindProperty("commissionUI").objectReferenceValue = commissionUi;
            so.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
            so.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
            so.FindProperty("stock").objectReferenceValue = player.GetComponent<PigmentStock>();
            so.FindProperty("brush").objectReferenceValue = brush;
            so.FindProperty("seasons").objectReferenceValue = seasonClock;
            so.FindProperty("visual").objectReferenceValue = visual;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>
        /// Bastien Marlowe, marchante de arte, con su puesto en la plaza del pueblo (hueco reservado en BuildTown).
        /// El mostrador mira a la fuente; el personaje está a un lado para que el jugador llegue a hablarle.
        /// </summary>
        static void BuildArtDealer(Transform hud, Transform town, DialogueUI dialogueUi, GameObject player, GameObject rig, PaintBrushController brush, SeasonClock seasonClock)
        {
            // Panel de venta.
            var list = BuildListPanel(hud, "ArtDealerUI", "Sell paintings", new Vector2(760f, 640f));
            var dealerUi = list.Root.AddComponent<ArtDealerUI>();
            var dealerSo = new SerializedObject(dealerUi);
            SetModalPanelRefs(dealerSo, list, player, rig);
            dealerSo.FindProperty("inventory").objectReferenceValue = player.GetComponent<PlayerInventory>();
            dealerSo.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
            dealerSo.FindProperty("messageLabel").objectReferenceValue = list.Message;
            dealerSo.ApplyModifiedPropertiesWithoutUndo();

            // Datos del personaje (sin encargos).
            if (!AssetDatabase.IsValidFolder($"{Root}/Data/Npcs"))
                AssetDatabase.CreateFolder($"{Root}/Data", "Npcs");
            var definitionPath = $"{Root}/Data/Npcs/Npc_ArtDealer.asset";
            var definition = AssetDatabase.LoadAssetAtPath<NpcDefinition>(definitionPath);
            if (definition == null)
            {
                definition = ScriptableObject.CreateInstance<NpcDefinition>();
                AssetDatabase.CreateAsset(definition, definitionPath);
            }
            definition.EditorSetup("Bastien Marlowe", new[]
            {
                "Hm. Let me guess: you paint, you grow, and now you would like to be paid. Bastien Marlowe. I appraise things.",
                "I buy originals only. Seeds and copies are of no interest to me. I pay by crop, quality, rarity and canvas, and I can tell all four at a glance.",
                "Show me something worth my time."
            }, new CommissionDefinition[0]);
            definition.EditorSetSeasonLines(new[]
            {
                "Spring. Everyone paints blossoms. Few paint them well.",
                "Summer. Bright colours sell. Muddy ones don't.",
                "Autumn. Collectors grow sentimental this time of year. Good for business.",
                "Winter. Fewer buyers, sharper eyes. Bring me your best."
            });
            EditorUtility.SetDirty(definition);

            // Puesto: mostrador con dos postes y toldo, mirando a la fuente (0, 0, -16). Frente = +Z local, postes atrás.
            var counterMat = GetOrCreateMaterial("M_Easel_Wood", new Color(0.42f, 0.28f, 0.18f));
            var awningMat = GetOrCreateMaterial("M_Town_Awning", new Color(0.32f, 0.42f, 0.51f));
            var frameMat = GetOrCreateMaterial("M_Gallery_Frame", new Color(0.25f, 0.17f, 0.11f));
            var canvasMat = GetOrCreateMaterial("M_Gallery_Canvas", new Color(0.95f, 0.93f, 0.88f));
            var stallPos = new Vector3(-3f, 0f, -13f);
            var yaw = Quaternion.Euler(0f, 135f, 0f);
            var stall = new GameObject("ArtDealerStall");
            stall.transform.SetParent(town, false);
            stall.transform.SetPositionAndRotation(stallPos, yaw);
            var box = stall.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, 0.45f, 0f);
            box.size = new Vector3(1.8f, 0.9f, 0.6f);

            CreatePart(PrimitiveType.Cube, "Counter", stall.transform, new Vector3(0f, 0.45f, 0f), new Vector3(1.8f, 0.9f, 0.6f), counterMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Post_Left", stall.transform, new Vector3(-0.85f, 1.25f, -0.25f), new Vector3(0.08f, 2.5f, 0.08f), counterMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Post_Right", stall.transform, new Vector3(0.85f, 1.25f, -0.25f), new Vector3(0.08f, 2.5f, 0.08f), counterMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Awning", stall.transform, new Vector3(0f, 2.45f, 0.05f), new Vector3(2f, 0.08f, 0.9f), awningMat, Quaternion.Euler(12f, 0f, 0f));

            // Marquitos decorativos apoyados en el mostrador (sin collider).
            for (int i = 0; i < 3; i++)
            {
                float x = -0.55f + i * 0.55f;
                float h = 0.30f + (i == 1 ? 0.08f : 0f);
                var frame = CreatePart(PrimitiveType.Cube, $"Frame_{i + 1}", stall.transform, new Vector3(x, 0.9f + h * 0.5f, -0.08f), new Vector3(0.4f, h, 0.03f), frameMat, Quaternion.Euler(-12f, 0f, 0f));
                CreatePart(PrimitiveType.Cube, "Canvas", frame.transform, new Vector3(0f, 0f, 0.6f), new Vector3(0.82f, 0.78f, 0.5f), canvasMat, Quaternion.identity);
            }

            // Figura de ~1,75 m a un lado del puesto, mirando a la plaza.
            var coatMat = GetOrCreateMaterial("M_Dealer_Coat", new Color(0.16f, 0.20f, 0.24f));
            var skinMat = GetOrCreateMaterial("M_Dealer_Skin", new Color(0.86f, 0.68f, 0.55f));
            var capMat = GetOrCreateMaterial("M_Dealer_Cap", new Color(0.30f, 0.22f, 0.16f));
            var cravatMat = GetOrCreateMaterial("M_Dealer_Cravat", new Color(0.72f, 0.62f, 0.30f));

            var npc = new GameObject("Npc_ArtDealer");
            npc.transform.SetParent(town, false);
            npc.transform.SetPositionAndRotation(stallPos + yaw * new Vector3(-1.5f, 0f, 0.1f), yaw);
            var capsule = npc.AddComponent<CapsuleCollider>();
            capsule.center = new Vector3(0f, 0.875f, 0f);
            capsule.radius = 0.3f;
            capsule.height = 1.75f;

            var visual = new GameObject("Visual").transform; // ver Ottilie: el cuerpo respira
            visual.SetParent(npc.transform, false);
            CreatePart(PrimitiveType.Capsule, "Coat", visual, new Vector3(0f, 0.6f, 0f), new Vector3(0.5f, 0.6f, 0.5f), coatMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Cravat", visual, new Vector3(0f, 1.2f, 0.14f), new Vector3(0.1f, 0.18f, 0.04f), cravatMat, Quaternion.identity);
            CreatePart(PrimitiveType.Sphere, "Head", visual, new Vector3(0f, 1.43f, 0f), Vector3.one * 0.26f, skinMat, Quaternion.identity);
            CreatePart(PrimitiveType.Sphere, "Cap", visual, new Vector3(0f, 1.53f, 0f), new Vector3(0.29f, 0.14f, 0.29f), capMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Cap_Visor", visual, new Vector3(0f, 1.5f, 0.15f), new Vector3(0.2f, 0.015f, 0.14f), capMat, Quaternion.identity);

            var component = npc.AddComponent<Npc>();
            var so = new SerializedObject(component);
            so.FindProperty("definition").objectReferenceValue = definition;
            so.FindProperty("dialogueUI").objectReferenceValue = dialogueUi;
            so.FindProperty("dealerUI").objectReferenceValue = dealerUi;
            so.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
            so.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
            so.FindProperty("stock").objectReferenceValue = player.GetComponent<PigmentStock>();
            so.FindProperty("brush").objectReferenceValue = brush;
            so.FindProperty("seasons").objectReferenceValue = seasonClock;
            so.FindProperty("visual").objectReferenceValue = visual;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>
        /// Festival de temporada en la plaza: puesto del juez en el lado sureste (mirando a la fuente), banderines y,
        /// en la galería, una vitrina baja en la pared oeste con un trofeo por estación. Puesto y banderines solo existen durante el festival.
        /// </summary>
        static void BuildFestival(Transform town, Transform gallery, DialogueUI dialogueUi, CommissionUI commissionUi, GameObject player, PaintBrushController brush, SeasonClock seasonClock)
        {
            var woodMat = GetOrCreateMaterial("M_Easel_Wood", new Color(0.42f, 0.28f, 0.18f));
            var galleryWoodMat = GetOrCreateMaterial("M_Gallery_Frame", new Color(0.25f, 0.17f, 0.11f));
            var awningMat = GetOrCreateMaterial("M_Festival_Awning", new Color(0.82f, 0.36f, 0.36f));
            var goldMat = GetOrCreateMaterial("M_Festival_Gold", new Color(0.85f, 0.70f, 0.30f));

            // Concursos por estación (orden del enum Season); los de pigmento piden el color de temporada.
            if (!AssetDatabase.IsValidFolder($"{Root}/Data/Npcs"))
                AssetDatabase.CreateFolder($"{Root}/Data", "Npcs");
            var sunflower = GetOrCreateSunflowerCrop();
            var seasonData = new[]
            {
                (Season.Spring, "blossom_pink", "Blossom Pink", new Color(0.93f, 0.62f, 0.70f), (CropDefinition)null, PaintingQuality.Good,
                    "The blossoms are out and so is the festival! Enter any painting with Blossom Pink, Good quality or better.",
                    "Petals on the breeze, and a pink ribbon for you!"),
                (Season.Summer, "sky_blue", "Sky Blue", new Color(0.55f, 0.75f, 0.92f), sunflower, PaintingQuality.Excellent,
                    "Summer festival, warm and bright! This year the judges want a sunflower painting, Excellent quality or better.",
                    "Pure sunshine on canvas! A blue ribbon for you."),
                (Season.Autumn, "burnt_orange", "Burnt Orange", new Color(0.80f, 0.42f, 0.15f), (CropDefinition)null, PaintingQuality.Good,
                    "Leaves are turning and the lanterns are lit! Enter any painting with Burnt Orange, Good quality or better.",
                    "Cosy as a bonfire! An orange ribbon for you."),
                (Season.Winter, "frost_lilac", "Frost Lilac", new Color(0.76f, 0.72f, 0.88f), (CropDefinition)null, PaintingQuality.Good,
                    "Warm cocoa, cold noses, and a festival! Enter any painting with Frost Lilac, Good quality or better.",
                    "Like frost on a window! A lilac ribbon for you.")
            };
            var contests = new CommissionDefinition[seasonData.Length];
            var trophies = new GameObject[seasonData.Length];
            var seasonMats = new Material[seasonData.Length];
            var shelfPos = new Vector3(-5.7f, 0f, 10f);
            CreateBlock("Trophy_Shelf", gallery, shelfPos + new Vector3(0f, 0.45f, 0f), new Vector3(0.4f, 0.9f, 1.4f), galleryWoodMat);
            for (int i = 0; i < seasonData.Length; i++)
            {
                var (season, id, pigmentName, color, crop, quality, request, thanks) = seasonData[i];
                var pigment = crop == null ? GetOrCreatePigment(id, pigmentName, color) : null;
                contests[i] = GetOrCreateCommission($"Commission_Festival_{season}", crop, null, quality,
                    new[] { request }, new[] { thanks, $"A {season} trophy now sits in your gallery." }, 120, 60, null, 0, null, pigment);
                seasonMats[i] = GetOrCreateMaterial($"M_Festival_{season}", color);

                // Copa de trofeo (base, pie y copa) sobre la vitrina; oculta hasta ganar el concurso.
                var trophy = new GameObject($"Trophy_{season}").transform;
                trophy.SetParent(gallery, false);
                trophy.localPosition = shelfPos + new Vector3(0f, 0.9f, -0.45f + i * 0.3f);
                CreatePart(PrimitiveType.Cylinder, "Base", trophy, new Vector3(0f, 0.015f, 0f), new Vector3(0.14f, 0.015f, 0.14f), goldMat, Quaternion.identity);
                CreatePart(PrimitiveType.Cylinder, "Stem", trophy, new Vector3(0f, 0.1f, 0f), new Vector3(0.04f, 0.07f, 0.04f), goldMat, Quaternion.identity);
                CreatePart(PrimitiveType.Sphere, "Cup", trophy, new Vector3(0f, 0.24f, 0f), Vector3.one * 0.16f, seasonMats[i], Quaternion.identity);
                trophies[i] = trophy.gameObject;
            }

            // Raíz siempre activa en (3.4, 0, -18.6), libre de bancos (3.9, -16) y farola (4.6, -20.6); el frente (+Z) mira a la fuente.
            var root = new GameObject("FestivalStand");
            root.transform.SetParent(town, false);
            var standPos = new Vector3(3.4f, 0f, -18.6f);
            root.transform.SetPositionAndRotation(standPos, Quaternion.LookRotation(new Vector3(0f, 0f, -16f) - standPos));

            var stall = new GameObject("Stall");
            stall.transform.SetParent(root.transform, false);
            var box = stall.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, 0.45f, 0f);
            box.size = new Vector3(1.8f, 0.9f, 0.6f);
            CreatePart(PrimitiveType.Cube, "Counter", stall.transform, new Vector3(0f, 0.45f, 0f), new Vector3(1.8f, 0.9f, 0.6f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Post_Left", stall.transform, new Vector3(-0.85f, 1.25f, -0.25f), new Vector3(0.08f, 2.5f, 0.08f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Post_Right", stall.transform, new Vector3(0.85f, 1.25f, -0.25f), new Vector3(0.08f, 2.5f, 0.08f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Awning", stall.transform, new Vector3(0f, 2.45f, 0.05f), new Vector3(2f, 0.08f, 0.9f), awningMat, Quaternion.Euler(12f, 0f, 0f));
            CreatePart(PrimitiveType.Cylinder, "Rosette", stall.transform, new Vector3(0f, 0.65f, 0.31f), new Vector3(0.3f, 0.01f, 0.3f), goldMat, Quaternion.Euler(90f, 0f, 0f));

            // Banderines: dos postes al norte de la plaza y las farolas del sur como anclas de cuatro cuerdas.
            // Hijo del pueblo (no del puesto, que está girado): las posiciones son de mundo = locales del pueblo.
            var bunting = new GameObject("Bunting").transform;
            bunting.SetParent(town, false);
            var northWest = new Vector3(-4.8f, 3f, -11.2f);
            var northEast = new Vector3(4.8f, 3f, -11.2f);
            var southWest = new Vector3(-4.6f, 3f, -20.6f);
            var southEast = new Vector3(4.6f, 3f, -20.6f);
            foreach (var top in new[] { northWest, northEast })
                CreatePart(PrimitiveType.Cylinder, "Pole", bunting, new Vector3(top.x, top.y * 0.5f, top.z), new Vector3(0.1f, top.y * 0.5f, 0.1f), woodMat, Quaternion.identity);
            BuildBuntingLine(bunting, northWest, northEast, woodMat, seasonMats);
            BuildBuntingLine(bunting, southWest, southEast, woodMat, seasonMats);
            BuildBuntingLine(bunting, northWest, southWest, woodMat, seasonMats);
            BuildBuntingLine(bunting, northEast, southEast, woodMat, seasonMats);

            var component = root.AddComponent<FestivalStand>();
            var so = new SerializedObject(component);
            so.FindProperty("clock").objectReferenceValue = seasonClock;
            SetArray(so.FindProperty("contests"), contests);
            SetArray(so.FindProperty("trophies"), trophies);
            SetArray(so.FindProperty("festivalVisuals"), new Object[] { stall, bunting.gameObject });
            so.FindProperty("dialogueUI").objectReferenceValue = dialogueUi;
            so.FindProperty("commissionUI").objectReferenceValue = commissionUi;
            so.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
            so.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
            so.FindProperty("stock").objectReferenceValue = player.GetComponent<PigmentStock>();
            so.FindProperty("brush").objectReferenceValue = brush;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Cuerda entre dos puntos con gallardetes (rombos) de colores colgando a intervalos.</summary>
        static void BuildBuntingLine(Transform parent, Vector3 from, Vector3 to, Material ropeMat, Material[] flagMats)
        {
            var dir = to - from;
            var look = Quaternion.LookRotation(dir);
            CreatePart(PrimitiveType.Cube, "Rope", parent, (from + to) * 0.5f, new Vector3(0.02f, 0.02f, dir.magnitude), ropeMat, look);
            int count = Mathf.FloorToInt(dir.magnitude / 0.8f);
            for (int i = 0; i < count; i++)
                CreatePart(PrimitiveType.Cube, "Flag", parent, Vector3.Lerp(from, to, (i + 0.5f) / count) + Vector3.down * 0.17f,
                    new Vector3(0.22f, 0.22f, 0.015f), flagMats[i % flagMats.Length], look * Quaternion.Euler(0f, 90f, 45f));
        }

        /// <summary>
        /// Tablón de encargos de los vecinos, en el lado oeste de la plaza, mirando a la fuente.
        /// Frente = +Z local (yaw 90 hacia +X); sólido, con tres notas que desaparecen al cumplir los encargos.
        /// </summary>
        static void BuildNoticeBoard(Transform town, DialogueUI dialogueUi, CommissionUI commissionUi, GameObject player, PaintBrushController brush)
        {
            var woodMat = GetOrCreateMaterial("M_Easel_Wood", new Color(0.42f, 0.28f, 0.18f));
            var corkMat = GetOrCreateMaterial("M_Gallery_Board", new Color(0.72f, 0.52f, 0.32f));
            var roofMat = GetOrCreateMaterial("M_Town_Roof", new Color(0.66f, 0.37f, 0.28f));
            var noteMat = GetOrCreateMaterial("M_Town_Note", new Color(0.93f, 0.89f, 0.78f));

            // Encargos de los vecinos (assets en Data/Npcs).
            if (!AssetDatabase.IsValidFolder($"{Root}/Data/Npcs"))
                AssetDatabase.CreateFolder($"{Root}/Data", "Npcs");
            var tomato = GetOrCreateCommission("Commission_TownTomato", GetOrCreateTomatoCrop(), null, PaintingQuality.Good, new[]
            {
                "Wanted: one tomato painting, Good quality or better, to brighten my shop window. Nothing sells bread like a little colour.",
                "- Mabel, the baker"
            }, new[]
            {
                "A note is pinned in reply: \"It is perfect! The whole street has stopped to look at it. Thank you, dear painter.\"",
                "- Mabel, the baker"
            }, 35, 20);
            var glowbell = GetOrCreateCommission("Commission_TownGlowbell", GetOrCreateGlowbellCrop(), null, PaintingQuality.Good, new[]
            {
                "Seeking a glowbell painting, Good quality or better. The nights are long and my lamps could use some company.",
                "- Ned, the lamplighter"
            }, new[]
            {
                "A note is pinned in reply: \"Hung it by my door. It glows almost as nicely as the real thing. Much obliged!\"",
                "- Ned, the lamplighter"
            }, 70, 40);
            var redSunflower = GetOrCreateCommission("Commission_TownRedSunflower", GetOrCreateSunflowerCrop(), "red", PaintingQuality.Good, new[]
            {
                "Please can someone paint a RED sunflower? Red is my favourite colour in the whole world. I can pay with my savings!",
                "- Pip, age 7"
            }, new[]
            {
                "A note is pinned in reply: \"It is the best painting ever!!! I showed everyone. Thank you thank you thank you!\"",
                "- Pip, age 7"
            }, 60, 40);

            var washStyle = System.Array.Find(GetOrCreateStyles(), s => s.Kind == StyleKind.Wash);
            var washGlowbell = GetOrCreateCommission("Commission_TownWashGlowbell", GetOrCreateGlowbellCrop(), null, PaintingQuality.Good, new[]
            {
                "Wanted: a glowbell painting in a soft watercolour Wash style, Good quality or better. The children would love it in our classroom. The shop sells the Wash style.",
                "- Rosalind, the schoolteacher"
            }, new[]
            {
                "A note is pinned in reply: \"The whole class gasped when we hung it. So gentle and so glowy. Thank you!\"",
                "- Rosalind, the schoolteacher"
            }, 90, 60, null, 0, washStyle);

            // Raíz a (-4.6, 0, -17.5), libre de banco, farola (-4.6, 0, -20.6) y puesto (-3, 0, -13).
            var root = new GameObject("CommissionBoard");
            root.transform.SetParent(town, false);
            root.transform.SetPositionAndRotation(new Vector3(-4.6f, 0f, -17.5f), Quaternion.Euler(0f, 90f, 0f));
            var box = root.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, 1.2f, 0f);
            box.size = new Vector3(2.0f, 2.4f, 0.4f);

            CreatePart(PrimitiveType.Cube, "Post_Left", root.transform, new Vector3(-0.9f, 1.1f, 0f), new Vector3(0.1f, 2.2f, 0.1f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Post_Right", root.transform, new Vector3(0.9f, 1.1f, 0f), new Vector3(0.1f, 2.2f, 0.1f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Cork", root.transform, new Vector3(0f, 1.4f, 0.02f), new Vector3(1.7f, 1.1f, 0.06f), corkMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Roof", root.transform, new Vector3(0f, 2.3f, 0.05f), new Vector3(2.2f, 0.07f, 0.6f), roofMat, Quaternion.Euler(10f, 0f, 0f));

            // Notas de papel clavadas al corcho (sin collider).
            var noteSpots = new[]
            {
                (new Vector3(-0.5f, 1.55f, 0.06f), 5f),
                (new Vector3(0.1f, 1.3f, 0.06f), -4f),
                (new Vector3(0.55f, 1.6f, 0.06f), 7f),
                (new Vector3(-0.1f, 1.68f, 0.065f), -6f)
            };
            var notes = new GameObject[noteSpots.Length];
            for (int i = 0; i < noteSpots.Length; i++)
            {
                var (position, angle) = noteSpots[i];
                notes[i] = CreatePart(PrimitiveType.Cube, $"Note_{i + 1}", root.transform, position, new Vector3(0.38f, 0.5f, 0.01f), noteMat, Quaternion.Euler(0f, 0f, angle));
            }

            var component = root.AddComponent<CommissionBoard>();
            var so = new SerializedObject(component);
            SetArray(so.FindProperty("commissions"), new[] { tomato, glowbell, redSunflower, washGlowbell });
            so.FindProperty("dialogueUI").objectReferenceValue = dialogueUi;
            so.FindProperty("commissionUI").objectReferenceValue = commissionUi;
            so.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
            so.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
            so.FindProperty("stock").objectReferenceValue = player.GetComponent<PigmentStock>();
            so.FindProperty("brush").objectReferenceValue = brush;
            SetArray(so.FindProperty("notes"), notes);
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Sets de la colección: el trío de jardín, uno por cultivo con variantes, las mutaciones y el híbrido.</summary>
        static CollectionSet[] GetOrCreateCollectionSets()
        {
            var crops = GetOrCreateCrops(); // girasol, tomate, glowbell, híbrido
            // Gold Leaf solo se consigue como recompensa: fuera de GetOrCreatePalette(), como Violet.
            var goldLeaf = GetOrCreatePigment("gold_leaf", "Gold Leaf", new Color(0.85f, 0.68f, 0.25f));

            var sets = new System.Collections.Generic.List<CollectionSet>
            {
                GetOrCreateCollectionSet("garden_trio", "Garden Trio", crops.Take(3).Select(c => new CollectionEntry { crop = c }).ToArray(), 60, 40)
            };
            foreach (var crop in crops.Take(3).Where(c => c.Variants.Length > 0))
                sets.Add(GetOrCreateCollectionSet($"{crop.Id}_varieties", $"{crop.DisplayName} Varieties",
                    crop.Variants.Select(v => new CollectionEntry { crop = crop, variantId = v.id }).ToArray(), 80, 50));
            sets.Add(GetOrCreateCollectionSet("oddities", "Oddities", Mutations.All.Select(m => new CollectionEntry { mutation = m }).ToArray(), 100, 60, goldLeaf, 30));
            sets.Add(GetOrCreateCollectionSet("cross_pollinator", "Cross-pollinator", new[] { new CollectionEntry { crop = crops[3] } }, 60, 40));
            return sets.ToArray();
        }

        static CollectionSet GetOrCreateCollectionSet(string id, string displayName, CollectionEntry[] entries, int rewardCoins, int rewardXp,
            PigmentDefinition rewardPigment = null, int rewardPigmentAmount = 0)
        {
            if (!AssetDatabase.IsValidFolder($"{Root}/Data/Collections"))
                AssetDatabase.CreateFolder($"{Root}/Data", "Collections");
            var path = $"{Root}/Data/Collections/Set_{id}.asset";
            var set = AssetDatabase.LoadAssetAtPath<CollectionSet>(path);
            if (set == null)
            {
                set = ScriptableObject.CreateInstance<CollectionSet>();
                AssetDatabase.CreateAsset(set, path);
            }
            set.EditorSetup(id, displayName, entries, rewardCoins, rewardXp, rewardPigment, rewardPigmentAmount);
            EditorUtility.SetDirty(set);
            return set;
        }

        static CommissionDefinition GetOrCreateCommission(string fileName, CropDefinition crop, string variantId, PaintingQuality minQuality,
            string[] requestLines, string[] thanksLines, int rewardCoins, int rewardXp, PigmentDefinition rewardPigment = null, int rewardPigmentAmount = 0,
            StyleDefinition style = null, PigmentDefinition requiredPigment = null)
        {
            var path = $"{Root}/Data/Npcs/{fileName}.asset";
            var commission = AssetDatabase.LoadAssetAtPath<CommissionDefinition>(path);
            if (commission == null)
            {
                commission = ScriptableObject.CreateInstance<CommissionDefinition>();
                AssetDatabase.CreateAsset(commission, path);
            }
            commission.EditorSetup(crop, variantId, minQuality, requestLines, thanksLines, rewardCoins, rewardXp, rewardPigment, rewardPigmentAmount, style, requiredPigment);
            EditorUtility.SetDirty(commission);
            return commission;
        }

        /// <summary>Tablón de corcho en el centro de la pared del fondo + panel con la colección de cultivos y variantes.</summary>
        static void BuildCollectionBoard(Transform hud, Transform gallery, GameObject player, GameObject rig, Material woodMat, PaintBrushController brush)
        {
            var corkMat = GetOrCreateMaterial("M_Gallery_Board", new Color(0.72f, 0.52f, 0.32f));

            var ui = BuildListPanel(hud, "CollectionUI", "Collection", new Vector2(760f, 640f));
            var collectionUi = ui.Root.AddComponent<CollectionUI>();
            var uiSo = new SerializedObject(collectionUi);
            SetModalPanelRefs(uiSo, ui, player, rig);
            uiSo.FindProperty("messageLabel").objectReferenceValue = ui.Message;
            uiSo.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
            uiSo.FindProperty("stock").objectReferenceValue = player.GetComponent<PigmentStock>();
            uiSo.FindProperty("brush").objectReferenceValue = brush;
            uiSo.ApplyModifiedPropertiesWithoutUndo();

            // Como los marcos: +Z local hacia la pared, el tablón se ve desde -Z.
            var board = new GameObject("CollectionBoard");
            board.transform.SetParent(gallery, false);
            board.transform.SetPositionAndRotation(new Vector3(0f, 1.6f, 13.9f), Quaternion.identity);

            var box = board.AddComponent<BoxCollider>();
            box.isTrigger = true;
            box.center = new Vector3(0f, 0f, -0.3f);
            box.size = new Vector3(2.4f, 1.7f, 0.6f);

            CreatePart(PrimitiveType.Cube, "Cork", board.transform, new Vector3(0f, 0f, -0.02f), new Vector3(2f, 1.3f, 0.04f), corkMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Border_Top", board.transform, new Vector3(0f, 0.7f, -0.04f), new Vector3(2.2f, 0.1f, 0.08f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Border_Bottom", board.transform, new Vector3(0f, -0.7f, -0.04f), new Vector3(2.2f, 0.1f, 0.08f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Border_Left", board.transform, new Vector3(-1.05f, 0f, -0.04f), new Vector3(0.1f, 1.3f, 0.08f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Border_Right", board.transform, new Vector3(1.05f, 0f, -0.04f), new Vector3(0.1f, 1.3f, 0.08f), woodMat, Quaternion.identity);

            // Tarjetas clavadas de adorno (sin collider).
            var cards = new[]
            {
                (new Vector3(-0.8f, 0.4f, -0.05f), 6f, new Color(0.98f, 0.85f, 0.35f)),
                (new Vector3(0.8f, 0.42f, -0.05f), -5f, new Color(0.95f, 0.5f, 0.4f)),
                (new Vector3(-0.85f, -0.4f, -0.05f), -4f, new Color(0.55f, 0.75f, 0.9f)),
                (new Vector3(0.85f, -0.38f, -0.05f), 7f, new Color(0.6f, 0.82f, 0.5f))
            };
            for (int i = 0; i < cards.Length; i++)
            {
                var (position, angle, color) = cards[i];
                var card = CreatePart(PrimitiveType.Cube, $"Card_{i + 1}", board.transform, position, new Vector3(0.3f, 0.4f, 0.01f),
                    GetOrCreateMaterial($"M_Gallery_Card_{i + 1}", color), Quaternion.Euler(0f, 0f, angle));
                Object.DestroyImmediate(card.GetComponent<Collider>());
            }

            // Canvas en el mundo: 1 unidad de UI = 1 mm.
            var canvasGo = new GameObject("Text", typeof(RectTransform), typeof(Canvas));
            canvasGo.transform.SetParent(board.transform, false);
            canvasGo.transform.localPosition = new Vector3(0f, 0f, -0.05f);
            canvasGo.transform.localScale = Vector3.one * 0.001f;
            ((RectTransform)canvasGo.transform).sizeDelta = new Vector2(1100f, 600f);
            canvasGo.GetComponent<Canvas>().renderMode = RenderMode.WorldSpace;

            var textGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
            textGo.transform.SetParent(canvasGo.transform, false);
            var textRect = (RectTransform)textGo.transform;
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.offsetMin = textRect.offsetMax = Vector2.zero;
            var label = textGo.GetComponent<Text>();
            label.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            label.alignment = TextAnchor.MiddleCenter;
            label.color = new Color(0.2f, 0.12f, 0.06f);
            label.resizeTextForBestFit = true;
            label.resizeTextMinSize = 20;
            label.resizeTextMaxSize = 200;
            label.raycastTarget = false;

            var component = board.AddComponent<CollectionBoard>();
            var so = new SerializedObject(component);
            so.FindProperty("collectionUI").objectReferenceValue = collectionUi;
            so.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
            SetArray(so.FindProperty("crops"), GetOrCreateCrops());
            SetArray(so.FindProperty("sets"), GetOrCreateCollectionSets());
            so.FindProperty("label").objectReferenceValue = label;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Marco de madera (hueco 1,5 x 1,2 m), cuadro oculto hasta colgar algo y placa con los datos debajo.</summary>
        static void BuildGalleryFrame(Transform parent, string name, Vector3 position, Quaternion rotation, Material woodMat,
            GalleryHangUI hangUi, PlayerInventory inventory)
        {
            var canvasMat = GetOrCreateMaterial("M_Gallery_Canvas", new Color(0.95f, 0.93f, 0.88f));
            var plaqueMat = GetOrCreateMaterial("M_Gallery_Plaque", new Color(0.78f, 0.63f, 0.32f));

            var frame = new GameObject(name);
            frame.transform.SetParent(parent, false);
            frame.transform.SetPositionAndRotation(position, rotation);

            // Volumen de interacción que sale de la pared hacia la sala (trigger: no estorba al jugador).
            var box = frame.AddComponent<BoxCollider>();
            box.isTrigger = true;
            box.center = new Vector3(0f, -0.1f, -0.3f);
            box.size = new Vector3(1.8f, 1.6f, 0.6f);

            CreatePart(PrimitiveType.Cube, "Backing", frame.transform, new Vector3(0f, 0f, -0.02f), new Vector3(1.5f, 1.2f, 0.04f), canvasMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Border_Top", frame.transform, new Vector3(0f, 0.65f, -0.04f), new Vector3(1.7f, 0.1f, 0.08f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Border_Bottom", frame.transform, new Vector3(0f, -0.65f, -0.04f), new Vector3(1.7f, 0.1f, 0.08f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Border_Left", frame.transform, new Vector3(-0.8f, 0f, -0.04f), new Vector3(0.1f, 1.2f, 0.08f), woodMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Border_Right", frame.transform, new Vector3(0.8f, 0f, -0.04f), new Vector3(0.1f, 1.2f, 0.08f), woodMat, Quaternion.identity);

            // El quad se ve desde -Z (la sala); GalleryFrame le da su propia instancia de material al colgar.
            var picture = CreatePart(PrimitiveType.Quad, "Picture", frame.transform, new Vector3(0f, 0f, -0.045f), new Vector3(1.4f, 1.1f, 1f), canvasMat, Quaternion.identity);
            Object.DestroyImmediate(picture.GetComponent<Collider>());

            var plaque = new GameObject("Plaque");
            plaque.transform.SetParent(frame.transform, false);
            plaque.transform.localPosition = new Vector3(0f, -0.93f, 0f);
            CreatePart(PrimitiveType.Cube, "Plate", plaque.transform, new Vector3(0f, 0f, -0.02f), new Vector3(1.2f, 0.3f, 0.04f), plaqueMat, Quaternion.identity);

            // Canvas en el mundo: 1 unidad de UI = 1 mm.
            var canvasGo = new GameObject("Text", typeof(RectTransform), typeof(Canvas));
            canvasGo.transform.SetParent(plaque.transform, false);
            canvasGo.transform.localPosition = new Vector3(0f, 0f, -0.045f);
            canvasGo.transform.localScale = Vector3.one * 0.001f;
            ((RectTransform)canvasGo.transform).sizeDelta = new Vector2(1200f, 300f);
            canvasGo.GetComponent<Canvas>().renderMode = RenderMode.WorldSpace;

            var textGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
            textGo.transform.SetParent(canvasGo.transform, false);
            var textRect = (RectTransform)textGo.transform;
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.offsetMin = new Vector2(20f, 0f);
            textRect.offsetMax = new Vector2(-20f, 0f);
            var label = textGo.GetComponent<Text>();
            label.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            label.alignment = TextAnchor.MiddleCenter;
            label.color = new Color(0.2f, 0.12f, 0.06f);
            label.resizeTextForBestFit = true;
            label.resizeTextMinSize = 20;
            label.resizeTextMaxSize = 110;
            label.raycastTarget = false;

            var component = frame.AddComponent<GalleryFrame>();
            var so = new SerializedObject(component);
            so.FindProperty("hangUI").objectReferenceValue = hangUi;
            so.FindProperty("inventory").objectReferenceValue = inventory;
            so.FindProperty("picture").objectReferenceValue = picture.GetComponent<MeshRenderer>();
            so.FindProperty("plaque").objectReferenceValue = plaque;
            so.FindProperty("plaqueText").objectReferenceValue = label;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Selector de cultivo al poner un lienzo en el caballete.</summary>
        static void BuildCropPicker(Transform hud, GameObject player, GameObject rig, SeasonClock seasonClock)
        {
            var ui = BuildListPanel(hud, "CropPickerUI", "What will you paint?", new Vector2(760f, 560f));
            Object.DestroyImmediate(ui.Message.gameObject);
            var so = new SerializedObject(ui.Root.AddComponent<CropPickerUI>());
            SetModalPanelRefs(so, ui, player, rig);
            so.FindProperty("seasons").objectReferenceValue = seasonClock;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static string BrushDescription(BrushKind kind) => kind switch
        {
            BrushKind.Fill => "Click a zone of the sketch to fill it in one go.",
            BrushKind.Glaze => "A see-through layer that mixes with the colors below.",
            _ => "A new brush for your palette."
        };

        /// <summary>Puesto de la tienda junto a la pared del fondo + panel de compra.</summary>
        static void BuildShop(Transform hud, Transform environment, GameObject player, GameObject rig, SeasonClock seasonClock)
        {
            // Filas de 80 px: caben 6 ofertas.
            var ui = BuildListPanel(hud, "ShopUI", "Shop", new Vector2(760f, 740f));
            var shop = ui.Root.AddComponent<ShopUI>();
            var so = new SerializedObject(shop);
            SetModalPanelRefs(so, ui, player, rig);
            SetArray(so.FindProperty("offers"), GetOrCreateShopOffers());
            so.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
            so.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
            so.FindProperty("seasons").objectReferenceValue = seasonClock;
            so.FindProperty("messageLabel").objectReferenceValue = ui.Message;
            so.ApplyModifiedPropertiesWithoutUndo();

            // Puesto placeholder: mostrador con dos postes y un toldo, mirando hacia el centro (-Z).
            var counterMat = GetOrCreateMaterial("M_Shop_Counter", new Color(0.34f, 0.52f, 0.46f));
            var awningMat = GetOrCreateMaterial("M_Accent_Terracotta", new Color(0.80f, 0.45f, 0.30f));
            var postMat = GetOrCreateMaterial("M_Easel_Wood", new Color(0.42f, 0.28f, 0.18f));
            var stall = new GameObject("ShopStall");
            stall.transform.SetParent(environment);
            stall.transform.localPosition = new Vector3(3.8f, 0f, 4.6f);
            var box = stall.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, 0.45f, 0f);
            box.size = new Vector3(1.8f, 0.9f, 0.6f);

            CreatePart(PrimitiveType.Cube, "Counter", stall.transform, new Vector3(0f, 0.45f, 0f), new Vector3(1.8f, 0.9f, 0.6f), counterMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Post_Left", stall.transform, new Vector3(-0.85f, 1.25f, 0.25f), new Vector3(0.08f, 2.5f, 0.08f), postMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Post_Right", stall.transform, new Vector3(0.85f, 1.25f, 0.25f), new Vector3(0.08f, 2.5f, 0.08f), postMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cube, "Awning", stall.transform, new Vector3(0f, 2.45f, -0.05f), new Vector3(2f, 0.08f, 0.9f), awningMat, Quaternion.Euler(-12f, 0f, 0f));
            var stallSo = new SerializedObject(stall.AddComponent<ShopStall>());
            stallSo.FindProperty("shop").objectReferenceValue = shop;
            stallSo.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Farol de obra gris (poste y cabeza) con luz cálida que se enciende al anochecer.</summary>
        static void BuildLantern(Transform parent, string name, Vector3 position)
        {
            var lampMat = GetOrCreateMaterial("M_Town_Lamp", new Color(0.16f, 0.15f, 0.15f));
            var lanternMat = GetOrCreateMaterial("M_Town_Lantern", new Color(0.32f, 0.29f, 0.24f));
            var root = new GameObject(name).transform;
            root.SetParent(parent, false);
            root.localPosition = position;
            CreatePart(PrimitiveType.Cylinder, "Post", root, new Vector3(0f, 1.1f, 0f), new Vector3(0.1f, 1.1f, 0.1f), lampMat, Quaternion.identity);
            var head = CreatePart(PrimitiveType.Cube, "Head", root, new Vector3(0f, 2.4f, 0f), new Vector3(0.3f, 0.4f, 0.3f), lanternMat, Quaternion.identity);
            var light = CreateLanternLight(root, new Vector3(0f, 2.3f, 0f), 6f);
            AddNightLamp(head, light, 0f, 2.5f, head.GetComponent<Renderer>(), lanternMat.GetColor("_BaseColor"));
        }

        /// <summary>Luz puntual cálida de farol, sin sombras; NightLamp la apaga de día.</summary>
        static Light CreateLanternLight(Transform parent, Vector3 localPosition, float range)
        {
            var go = new GameObject("Light");
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPosition;
            var light = go.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = new Color(1f, 0.76f, 0.48f); // #FFC27A
            light.range = range;
            light.intensity = 0f;
            light.shadows = LightShadows.None;
            return light;
        }

        /// <summary>Conecta una luz (opcional) y una bombilla (opcional) al ciclo día/noche de DayLighting.</summary>
        static void AddNightLamp(GameObject host, Light light, float dayIntensity, float nightIntensity, Renderer bulb, Color bulbDayColor)
        {
            var lamp = host.AddComponent<NightLamp>();
            var so = new SerializedObject(lamp);
            so.FindProperty("dayLighting").objectReferenceValue = Object.FindFirstObjectByType<DayLighting>();
            so.FindProperty("lampLight").objectReferenceValue = light;
            so.FindProperty("dayIntensity").floatValue = dayIntensity;
            so.FindProperty("nightIntensity").floatValue = nightIntensity;
            so.FindProperty("bulb").objectReferenceValue = bulb;
            if (bulb != null) so.FindProperty("bulbDayColor").colorValue = bulbDayColor;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Volumen local de zona: caja trigger con un perfil propio que corrige temperatura y saturación sobre el global.</summary>
        static void BuildZoneVolume(string name, Vector3 center, Vector3 size, string profilePath, float temperatureDelta, float saturationDelta)
        {
            AssetDatabase.DeleteAsset(profilePath);
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(profile, profilePath);
            AddOverride<WhiteBalance>(profile).temperature.Override(GlobalTemperature + temperatureDelta);
            AddOverride<ColorAdjustments>(profile).saturation.Override(GlobalSaturation + saturationDelta);
            EditorUtility.SetDirty(profile);

            var go = new GameObject(name);
            go.transform.position = center;
            var box = go.AddComponent<BoxCollider>();
            box.isTrigger = true;
            box.size = size;
            var volume = go.AddComponent<Volume>();
            volume.isGlobal = false;
            volume.blendDistance = 1.5f;
            volume.priority = 1f;
            volume.sharedProfile = profile;
        }

        /// <summary>Lámpara de prueba sobre la mesa (Fase 1C).</summary>
        static void BuildTestLamp(Transform parent, Vector3 position)
        {
            var lamp = new GameObject("TestLamp");
            lamp.transform.SetParent(parent);
            lamp.transform.localPosition = position;

            var stand = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            stand.name = "Stand";
            stand.transform.SetParent(lamp.transform, false);
            stand.transform.localPosition = new Vector3(0f, 0.2f, 0f);
            stand.transform.localScale = new Vector3(0.08f, 0.2f, 0.08f);
            stand.GetComponent<MeshRenderer>().sharedMaterial = GetOrCreateMaterial("M_Player_Visor", new Color(0.15f, 0.12f, 0.1f));

            var bulb = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            bulb.name = "Bulb";
            bulb.transform.SetParent(lamp.transform, false);
            bulb.transform.localPosition = new Vector3(0f, 0.48f, 0f);
            bulb.transform.localScale = Vector3.one * 0.22f;
            bulb.GetComponent<MeshRenderer>().sharedMaterial = GetOrCreateMaterial("M_Lamp_Bulb", new Color(0.35f, 0.33f, 0.3f));

            var lightGo = new GameObject("Light");
            lightGo.transform.SetParent(lamp.transform, false);
            lightGo.transform.localPosition = new Vector3(0f, 0.48f, 0f);
            var light = lightGo.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = new Color(1f, 0.8f, 0.5f);
            light.range = 5f;
            light.intensity = 3f;

            var testLamp = lamp.AddComponent<TestLamp>();
            var so = new SerializedObject(testLamp);
            so.FindProperty("lampLight").objectReferenceValue = light;
            so.FindProperty("bulb").objectReferenceValue = bulb.GetComponent<MeshRenderer>();
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Conecta los ejes "Look" de la cámara a nuestra acción Player/Look y apaga el resto (zoom).</summary>
        static void AddLookInput(GameObject cameraGo)
        {
            var input = cameraGo.AddComponent<CinemachineInputAxisController>();
            input.SynchronizeControllers();
            var look = GetAction("Player/Look");
            foreach (var c in input.Controllers)
            {
                bool isLook = c.Name.Contains("Look");
                c.Enabled = isLook;
                if (!isLook) continue;
                c.Input.InputAction = look;
                c.Input.Gain = c.Name.Contains("Y") ? -1f : 1f;
            }
        }

        static InputActionReference GetAction(string mapAndAction) =>
            AssetDatabase.LoadAllAssetsAtPath(ControlsPath)
                .OfType<InputActionReference>()
                .First(r => r.name == mapAndAction);

        static GameObject CreateBlock(string name, Transform parent, Vector3 position, Vector3 scale, Material material)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false); // false: bajo un padre girado (casas, bancos) gira con él
            go.transform.localPosition = position;
            go.transform.localScale = scale;
            go.GetComponent<MeshRenderer>().sharedMaterial = material;
            go.isStatic = true;
            return go;
        }

        static void CreateBoundary(string name, Transform parent, Vector3 position, Vector3 size)
        {
            // Capa "Ignore Raycast": bloquea al jugador pero la cámara puede verse a través.
            var go = new GameObject(name) { layer = 2 };
            go.transform.SetParent(parent);
            go.transform.localPosition = position;
            go.AddComponent<BoxCollider>().size = size;
            go.isStatic = true;
        }

        static Material GetOrCreateMaterial(string name, Color color)
        {
            var path = $"{MaterialsFolder}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null)
            {
                mat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                AssetDatabase.CreateAsset(mat, path);
            }
            mat.SetColor("_BaseColor", color);
            mat.SetFloat("_Smoothness", 0.15f);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static VolumeProfile CreateVolumeProfile()
        {
            AssetDatabase.DeleteAsset(ProfilePath);
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(profile, ProfilePath);

            var bloom = AddOverride<Bloom>(profile);
            bloom.intensity.Override(0.4f);
            bloom.threshold.Override(1f);
            bloom.scatter.Override(0.7f);

            var tonemapping = AddOverride<Tonemapping>(profile);
            tonemapping.mode.Override(TonemappingMode.Neutral);

            var whiteBalance = AddOverride<WhiteBalance>(profile);
            whiteBalance.temperature.Override(GlobalTemperature);

            var colorAdjustments = AddOverride<ColorAdjustments>(profile);
            colorAdjustments.saturation.Override(GlobalSaturation);
            colorAdjustments.contrast.Override(5f);

            var vignette = AddOverride<Vignette>(profile);
            vignette.intensity.Override(0.2f);

            EditorUtility.SetDirty(profile);
            return profile;
        }

        static T AddOverride<T>(VolumeProfile profile) where T : VolumeComponent
        {
            var component = profile.Add<T>(true);
            component.hideFlags = HideFlags.HideInInspector | HideFlags.HideInHierarchy;
            AssetDatabase.AddObjectToAsset(component, profile);
            return component;
        }
    }
}
