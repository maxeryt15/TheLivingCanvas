using System.Linq;
using TheLivingCanvas.Core;
using TheLivingCanvas.Data;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Growth;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Player;
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
        const string ControlsPath = Root + "/Settings/PlayerControls.inputactions";
        const string PlayerPrefabPath = Root + "/Prefabs/Player/Player.prefab";
        const string EaselPrefabPath = Root + "/Prefabs/Canvas/Easel.prefab";
        const string PaintingPlotPrefabPath = Root + "/Prefabs/Crops/PaintingPlot.prefab";
        const string SunflowerPrefabPath = Root + "/Prefabs/Crops/Sunflower.prefab";
        const string TomatoPrefabPath = Root + "/Prefabs/Crops/Tomato.prefab";
        const string GlowbellPrefabPath = Root + "/Prefabs/Crops/Glowbell.prefab";

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
            CreateBlock("Wall_Back", environment.transform, new Vector3(0f, 1.5f, 6f), new Vector3(12f, 3f, 0.2f), wallMat);
            CreateBlock("Wall_Left", environment.transform, new Vector3(-6f, 1.5f, 0f), new Vector3(0.2f, 3f, 12f), wallMat);
            CreateBlock("Table", environment.transform, new Vector3(-4.5f, 0.4f, 4.5f), new Vector3(2f, 0.8f, 1f), accentMat);

            // Límites invisibles en los lados abiertos para no caerse del suelo.
            CreateBoundary("Boundary_Front", environment.transform, new Vector3(0f, 1.5f, -6f), new Vector3(12f, 3f, 0.2f));
            CreateBoundary("Boundary_Right", environment.transform, new Vector3(6f, 1.5f, 0f), new Vector3(0.2f, 3f, 12f));

            // Luz cálida de media tarde.
            var sunGo = new GameObject("Sun");
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.88f, 0.72f);
            sun.intensity = 1.6f;
            sun.shadows = LightShadows.Soft;
            sunGo.transform.rotation = Quaternion.Euler(40f, -35f, 0f);

            RenderSettings.sun = sun;
            RenderSettings.skybox = AssetDatabase.GetBuiltinExtraResource<Material>("Default-Skybox.mat");
            RenderSettings.ambientMode = AmbientMode.Skybox;

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
            var placer = BuildPaintingPlacer(hud.transform, player);
            BuildInventoryUI(hud.transform, player.GetComponent<PlayerInventory>(), placer, paintMode,
                rig.GetComponent<CursorLock>(), rig.GetComponent<CameraModeController>());
            BuildCoinCounter(hud.transform, player.GetComponent<Wallet>());
            BuildTestLamp(environment.transform, new Vector3(-4.5f, 0.8f, 4.2f));
            BuildSellCrate(environment.transform, new Vector3(-4.6f, 0f, 1.5f));
            BuildShop(hud.transform, environment.transform, player, rig);
            BuildCropPicker(hud.transform, player, rig);

            // Caballete delante del punto de inicio, mirando hacia el jugador.
            var easel = (GameObject)PrefabUtility.InstantiatePrefab(BuildEaselPrefab());
            easel.transform.SetPositionAndRotation(new Vector3(1.5f, 0f, 1.5f), Quaternion.Euler(0f, 200f, 0f));

            var volumeGo = new GameObject("Global Volume");
            var volume = volumeGo.AddComponent<Volume>();
            volume.isGlobal = true;
            volume.sharedProfile = CreateVolumeProfile();

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

            root.AddComponent<PlayerInventory>();
            root.AddComponent<Wallet>();
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

            new GameObject("CameraTarget").transform.SetParent(root.transform, false);
            root.transform.Find("CameraTarget").localPosition = new Vector3(0f, 1.4f, 0f);
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

            // Tercera persona: órbita alrededor del jugador, con colisión contra paredes.
            var tpGo = new GameObject("CM ThirdPerson");
            tpGo.transform.SetParent(rig.transform, false);
            var tp = tpGo.AddComponent<CinemachineCamera>();
            tp.Follow = player.transform.Find("CameraTarget");
            tp.Priority = 10; // activa también en el editor; en juego la gestiona CameraModeController
            tp.Lens.FieldOfView = 55f;
            var orbit = tpGo.AddComponent<CinemachineOrbitalFollow>();
            orbit.OrbitStyle = CinemachineOrbitalFollow.OrbitStyles.Sphere;
            orbit.Radius = 4.5f;
            orbit.VerticalAxis.Value = 15f;
            tpGo.AddComponent<CinemachineRotationComposer>();
            var deoccluder = tpGo.AddComponent<CinemachineDeoccluder>();
            deoccluder.IgnoreTag = "Player";
            var avoid = deoccluder.AvoidObstacles;
            avoid.Enabled = true;
            avoid.CameraRadius = 0.2f;
            avoid.Strategy = CinemachineDeoccluder.ObstacleAvoidance.ResolutionStrategy.PullCameraForward;
            deoccluder.AvoidObstacles = avoid;
            AddLookInput(tpGo);

            // Primera persona: fija en los ojos, mirar con ratón/stick.
            var fpGo = new GameObject("CM FirstPerson");
            fpGo.transform.SetParent(rig.transform, false);
            var fp = fpGo.AddComponent<CinemachineCamera>();
            fp.Follow = player.transform.Find("EyePoint");
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
            so.FindProperty("thirdPersonCamera").objectReferenceValue = tp;
            so.FindProperty("firstPersonCamera").objectReferenceValue = fp;
            so.FindProperty("fixedViewCamera").objectReferenceValue = fixedCam;
            so.FindProperty("playerMovement").objectReferenceValue = player.GetComponent<PlayerMovement>();
            so.FindProperty("playerVisuals").objectReferenceValue = player.transform.Find("Visuals").gameObject;
            so.FindProperty("debugToggleAction").objectReferenceValue = GetAction("Player/ToggleView");
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
            brushSo.ApplyModifiedPropertiesWithoutUndo();

            // El mensaje vive en el HUD raíz para que la enhorabuena siga visible al salir del modo pintura.
            var finisher = paintMode.gameObject.AddComponent<PaintingFinisher>();
            var finisherSo = new SerializedObject(finisher);
            finisherSo.FindProperty("paintMode").objectReferenceValue = paintMode;
            finisherSo.FindProperty("feedback").objectReferenceValue = BuildFeedback(hud.transform);
            finisherSo.ApplyModifiedPropertiesWithoutUndo();

            BuildPalettePanel(paintHud.transform, brush, finisher);
            BuildCoverageReadout(paintHud.transform, paintMode, brush);
            return paintMode;
        }

        /// <summary>Colocar pinturas del inventario en el suelo: controlador, aviso y prefab de la parcela.</summary>
        static PaintingPlacer BuildPaintingPlacer(Transform hud, GameObject player)
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
            PaintModeController paintMode, CursorLock cursorLock, CameraModeController cameraMode)
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
                new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(760f, 520f));
            var title = AddStretchedText(panel.transform, "Title", 32, font, cream, TextAnchor.UpperCenter);
            title.text = "Inventory";
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
            gridRect.offsetMax = new Vector2(-30f, -70f);
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
            rect.anchoredPosition = new Vector2(-30f, -30f);
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
        static void BuildPalettePanel(Transform parent, PaintBrushController brush, PaintingFinisher finisher)
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
            panelRect.sizeDelta = new Vector2(240f, 860f);
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

            AddLabel(panel.transform, "SizeLabel", "Brush size", 24, 30f, font, cream);
            var slider = DefaultControls.CreateSlider(resources);
            slider.name = "SizeSlider";
            slider.transform.SetParent(panel.transform, false);
            slider.AddComponent<LayoutElement>().preferredHeight = 30f;

            var eraser = CreateButton(resources, panel.transform, "EraserButton", "Eraser", 24, font);
            ConfigureHighlight(eraser.AddComponent<Outline>(), cream);

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

            var tools = panel.AddComponent<PaintToolsUI>();
            var so = new SerializedObject(tools);
            so.FindProperty("brush").objectReferenceValue = brush;
            so.FindProperty("swatchContainer").objectReferenceValue = swatches.transform;
            so.FindProperty("swatchTemplate").objectReferenceValue = template.GetComponent<Button>();
            so.FindProperty("sizeSlider").objectReferenceValue = slider.GetComponent<Slider>();
            so.FindProperty("eraserButton").objectReferenceValue = eraser.GetComponent<Button>();
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

        static void AddLabel(Transform parent, string name, string content, int fontSize, float height, Font font, Color color)
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
        }

        /// <summary>Borde claro alrededor de la herramienta seleccionada (PaintToolsUI lo activa).</summary>
        static void ConfigureHighlight(Outline outline, Color color)
        {
            outline.effectColor = color;
            outline.effectDistance = new Vector2(4f, -4f);
            outline.enabled = false;
        }

        /// <summary>Los 6 pigmentos del vertical slice, en el orden de la paleta.</summary>
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

        static CropDefinition[] GetOrCreateCrops() => new[] { GetOrCreateSunflowerCrop(), GetOrCreateTomatoCrop(), GetOrCreateGlowbellCrop() };

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
            crop.EditorSetVariants(new[]
            {
                new CropVariant { id = "sun", displayName = "Sun Glowbell", zoneName = "Glow", pigment = palette[0], rarity = Rarity.Uncommon },
                new CropVariant { id = "ember", displayName = "Ember Glowbell", zoneName = "Glow", pigment = palette[4], rarity = Rarity.Rare },
            });
            EditorUtility.SetDirty(crop);
            return crop;
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

            var prefab = PrefabUtility.SaveAsPrefabAsset(root, SunflowerPrefabPath);
            Object.DestroyImmediate(root);
            return prefab.GetComponent<SunflowerPlant>();
        }

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

            var promptUi = hud.AddComponent<InteractionPromptUI>();
            var so = new SerializedObject(promptUi);
            so.FindProperty("interactor").objectReferenceValue = interactor;
            so.FindProperty("panel").objectReferenceValue = panel;
            so.FindProperty("label").objectReferenceValue = label;
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

        /// <summary>Ofertas de la tienda (assets en Data/Shop).</summary>
        static ShopOffer[] GetOrCreateShopOffers()
        {
            if (!AssetDatabase.IsValidFolder($"{Root}/Data/Shop"))
                AssetDatabase.CreateFolder($"{Root}/Data", "Shop");

            var canvasPath = $"{Root}/Data/Shop/Offer_Canvas.asset";
            var canvas = AssetDatabase.LoadAssetAtPath<CanvasOffer>(canvasPath);
            if (canvas == null)
            {
                canvas = ScriptableObject.CreateInstance<CanvasOffer>();
                AssetDatabase.CreateAsset(canvas, canvasPath);
            }
            canvas.EditorSetupOffer("Blank canvas", "A fresh canvas for the easel.", 5, null);
            EditorUtility.SetDirty(canvas);

            var offers = new System.Collections.Generic.List<ShopOffer> { canvas };
            foreach (var pigment in GetOrCreatePalette().Skip(StartingPigments))
            {
                var path = $"{Root}/Data/Shop/Offer_Pigment_{pigment.Id}.asset";
                var offer = AssetDatabase.LoadAssetAtPath<PigmentOffer>(path);
                if (offer == null)
                {
                    offer = ScriptableObject.CreateInstance<PigmentOffer>();
                    AssetDatabase.CreateAsset(offer, path);
                }
                offer.EditorSetupOffer(pigment.DisplayName, "A new color for your palette.", 15, null);
                offer.EditorSetPigment(pigment);
                EditorUtility.SetDirty(offer);
                offers.Add(offer);
            }
            foreach (var crop in GetOrCreateCrops().Skip(StartingCrops))
            {
                var path = $"{Root}/Data/Shop/Offer_Sketch_{crop.Id}.asset";
                var offer = AssetDatabase.LoadAssetAtPath<SketchOffer>(path);
                if (offer == null)
                {
                    offer = ScriptableObject.CreateInstance<SketchOffer>();
                    AssetDatabase.CreateAsset(offer, path);
                }
                offer.EditorSetupOffer($"{crop.DisplayName} sketch", $"Lets you paint {crop.DisplayName.ToLowerInvariant()}s on the easel.", 30, null);
                offer.EditorSetCrop(crop);
                EditorUtility.SetDirty(offer);
                offers.Add(offer);
            }
            return offers.ToArray();
        }

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

            var rowsGo = new GameObject("Rows", typeof(RectTransform), typeof(VerticalLayoutGroup));
            rowsGo.transform.SetParent(panel.transform, false);
            var rowsRect = (RectTransform)rowsGo.transform;
            rowsRect.anchorMin = Vector2.zero;
            rowsRect.anchorMax = Vector2.one;
            rowsRect.offsetMin = new Vector2(30f, 140f);
            rowsRect.offsetMax = new Vector2(-30f, -70f);
            var rowsLayout = rowsGo.GetComponent<VerticalLayoutGroup>();
            rowsLayout.spacing = 10f;
            rowsLayout.childControlWidth = rowsLayout.childControlHeight = true;
            rowsLayout.childForceExpandHeight = false;

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
            so.FindProperty("interactor").objectReferenceValue = player.GetComponent<PlayerInteractor>();
            so.FindProperty("cursorLock").objectReferenceValue = rig.GetComponent<CursorLock>();
            so.FindProperty("cameraMode").objectReferenceValue = rig.GetComponent<CameraModeController>();
            so.FindProperty("exitAction").objectReferenceValue = GetAction("Paint/Exit");
            so.FindProperty("panel").objectReferenceValue = ui.Panel;
            so.FindProperty("closeButton").objectReferenceValue = ui.Close;
            so.FindProperty("rowContainer").objectReferenceValue = ui.Rows;
            so.FindProperty("rowTemplate").objectReferenceValue = ui.RowTemplate;
        }

        /// <summary>Selector de cultivo al poner un lienzo en el caballete.</summary>
        static void BuildCropPicker(Transform hud, GameObject player, GameObject rig)
        {
            var ui = BuildListPanel(hud, "CropPickerUI", "What will you paint?", new Vector2(760f, 560f));
            Object.DestroyImmediate(ui.Message.gameObject);
            var so = new SerializedObject(ui.Root.AddComponent<CropPickerUI>());
            SetModalPanelRefs(so, ui, player, rig);
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Puesto de la tienda junto a la pared del fondo + panel de compra.</summary>
        static void BuildShop(Transform hud, Transform environment, GameObject player, GameObject rig)
        {
            // Filas de 80 px: caben 6 ofertas.
            var ui = BuildListPanel(hud, "ShopUI", "Shop", new Vector2(760f, 740f));
            var shop = ui.Root.AddComponent<ShopUI>();
            var so = new SerializedObject(shop);
            SetModalPanelRefs(so, ui, player, rig);
            SetArray(so.FindProperty("offers"), GetOrCreateShopOffers());
            so.FindProperty("wallet").objectReferenceValue = player.GetComponent<Wallet>();
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
            go.transform.SetParent(parent);
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
            whiteBalance.temperature.Override(12f);

            var colorAdjustments = AddOverride<ColorAdjustments>(profile);
            colorAdjustments.saturation.Override(10f);
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
