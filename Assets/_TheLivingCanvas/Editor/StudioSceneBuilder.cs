using System.Linq;
using TheLivingCanvas.Core;
using TheLivingCanvas.Data;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Gallery;
using TheLivingCanvas.Growth;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Npcs;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Player;
using TheLivingCanvas.Progression;
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
            // Pared del fondo con un vano de 2 m x 2,4 m en x = 0: da paso a la galería.
            CreateBlock("Wall_Back_Left", environment.transform, new Vector3(-3.5f, 1.5f, 6f), new Vector3(5f, 3f, 0.2f), wallMat);
            CreateBlock("Wall_Back_Right", environment.transform, new Vector3(3.5f, 1.5f, 6f), new Vector3(5f, 3f, 0.2f), wallMat);
            CreateBlock("Wall_Back_Lintel", environment.transform, new Vector3(0f, 2.7f, 6f), new Vector3(2f, 0.6f, 0.2f), wallMat);
            CreateBlock("Wall_Left", environment.transform, new Vector3(-6f, 1.5f, 0f), new Vector3(0.2f, 3f, 12f), wallMat);
            CreateBlock("Table", environment.transform, new Vector3(-4.5f, 0.4f, 4.5f), new Vector3(2f, 0.8f, 1f), accentMat);

            // Límites invisibles en los lados abiertos para no caerse del suelo.
            CreateBoundary("Boundary_Front", environment.transform, new Vector3(0f, 1.5f, -6f), new Vector3(12f, 3f, 0.2f));
            // El lado derecho deja un hueco de 2 m en z = 0: lo cierra la puerta del jardín.
            CreateBoundary("Boundary_Right_Front", environment.transform, new Vector3(6f, 1.5f, -3.5f), new Vector3(0.2f, 3f, 5f));
            CreateBoundary("Boundary_Right_Back", environment.transform, new Vector3(6f, 1.5f, 3.5f), new Vector3(0.2f, 3f, 5f));

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
                rig.GetComponent<CursorLock>(), rig.GetComponent<CameraModeController>(),
                paintMode.GetComponent<PaintBrushController>(), player.GetComponent<PigmentStock>());
            BuildCoinCounter(hud.transform, player.GetComponent<Wallet>());
            BuildLevelCounter(hud.transform, player.GetComponent<ArtistLevel>());
            BuildTestLamp(environment.transform, new Vector3(-4.5f, 0.8f, 4.2f));
            BuildSellCrate(environment.transform, new Vector3(-4.6f, 0f, 1.5f));
            BuildShop(hud.transform, environment.transform, player, rig);
            BuildCropPicker(hud.transform, player, rig);
            BuildMortar(hud.transform, environment.transform, player, rig, paintMode.GetComponent<PaintBrushController>());
            BuildGarden(player.GetComponent<ArtistLevel>());
            BuildGallery(hud.transform, player, rig, wallMat);

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
            // Solo el pincel redondo al empezar; el resto se compra en la tienda.
            SetArray(brushSo.FindProperty("brushes"), GetOrCreateBrushes().Take(StartingBrushes).ToArray());
            brushSo.ApplyModifiedPropertiesWithoutUndo();

            // El mensaje vive en el HUD raíz para que la enhorabuena siga visible al salir del modo pintura.
            var finisher = paintMode.gameObject.AddComponent<PaintingFinisher>();
            var finisherSo = new SerializedObject(finisher);
            finisherSo.FindProperty("paintMode").objectReferenceValue = paintMode;
            finisherSo.FindProperty("feedback").objectReferenceValue = BuildFeedback(hud.transform);
            finisherSo.FindProperty("brush").objectReferenceValue = brush;
            finisherSo.FindProperty("stock").objectReferenceValue = player.GetComponent<PigmentStock>();
            finisherSo.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
            finisherSo.ApplyModifiedPropertiesWithoutUndo();

            BuildPalettePanel(paintHud.transform, brush, finisher, player.GetComponent<PigmentStock>());
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
        static void BuildPalettePanel(Transform parent, PaintBrushController brush, PaintingFinisher finisher, PigmentStock stock)
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
            panelRect.sizeDelta = new Vector2(300f, 980f); // ancho para 4 botones en la fila de herramientas; alto: ver suma de la columna (960)
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
            var amount = AddStretchedText(template.transform, "Amount", 20, font, Color.white, TextAnchor.LowerRight);
            ((RectTransform)amount.transform).offsetMax = new Vector2(-6f, 0f);
            ((RectTransform)amount.transform).offsetMin = new Vector2(0f, 4f);
            var amountShadow = amount.gameObject.AddComponent<Shadow>(); // legible sobre el blanco y el amarillo
            amountShadow.effectColor = new Color(0f, 0f, 0f, 0.8f);
            amountShadow.effectDistance = new Vector2(1.5f, -1.5f);

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

            var tools = panel.AddComponent<PaintToolsUI>();
            var so = new SerializedObject(tools);
            so.FindProperty("brush").objectReferenceValue = brush;
            so.FindProperty("stock").objectReferenceValue = stock;
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
            crop.EditorSetPigmentYield(palette[4], 10);
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
            crop.EditorSetPigmentYield(palette[0], 10);
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
            };
        }

        static CanvasType GetOrCreateCanvasType(string id, string displayName, string description,
            int harvestMultiplier, float pigmentMultiplier, float plotScale)
        {
            var path = $"{Root}/Data/Canvases/Canvas_{id}.asset";
            var canvasType = AssetDatabase.LoadAssetAtPath<CanvasType>(path);
            if (canvasType == null)
            {
                canvasType = ScriptableObject.CreateInstance<CanvasType>();
                AssetDatabase.CreateAsset(canvasType, path);
            }
            canvasType.EditorSetup(id, displayName, description, harvestMultiplier, pigmentMultiplier, plotScale);
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

            foreach (var crop in GetOrCreateCrops().Skip(StartingCrops))
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
            foreach (var offer in offers)
            {
                offer.EditorSetRequiredLevel(RequiredLevel(offer.name));
                EditorUtility.SetDirty(offer);
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
        static void BuildGallery(Transform hud, GameObject player, GameObject rig, Material wallMat)
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
            }

            // Cada marco mira hacia dentro de la sala: su +Z local apunta a la pared.
            var inventory = player.GetComponent<PlayerInventory>();
            BuildGalleryFrame(gallery, "Frame_L1", new Vector3(-5.9f, 1.6f, 8.5f), Quaternion.Euler(0f, -90f, 0f), woodMat, hangUi, inventory);
            BuildGalleryFrame(gallery, "Frame_L2", new Vector3(-5.9f, 1.6f, 11.5f), Quaternion.Euler(0f, -90f, 0f), woodMat, hangUi, inventory);
            BuildGalleryFrame(gallery, "Frame_R1", new Vector3(5.9f, 1.6f, 8.5f), Quaternion.Euler(0f, 90f, 0f), woodMat, hangUi, inventory);
            BuildGalleryFrame(gallery, "Frame_R2", new Vector3(5.9f, 1.6f, 11.5f), Quaternion.Euler(0f, 90f, 0f), woodMat, hangUi, inventory);
            BuildGalleryFrame(gallery, "Frame_B1", new Vector3(-3.5f, 1.6f, 13.9f), Quaternion.identity, woodMat, hangUi, inventory);
            BuildGalleryFrame(gallery, "Frame_B2", new Vector3(3.5f, 1.6f, 13.9f), Quaternion.identity, woodMat, hangUi, inventory);
            BuildCollectionBoard(hud, gallery, player, rig, woodMat);
            BuildNpc(hud, gallery, player, rig);
        }

        /// <summary>Ottilie Vane, coleccionista excéntrica (figura de primitivas) + el panel de diálogo al pie de la pantalla.</summary>
        static void BuildNpc(Transform hud, Transform gallery, GameObject player, GameObject rig)
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
            definition.EditorSetup("Ottilie Vane", new[]
            {
                "Oh! A new face among my favourite walls. I'm Ottilie Vane, and I collect colours the way other people collect teaspoons.",
                "Rare pigments make my heart flutter. And paintings that grow? Darling, I would cross three counties for one.",
                "Keep your brushes wet and your garden wilder than is sensible. The best colours always sprout where nobody planned them.",
                "I may have a request or two for you, once you have settled in. Do come and chat again soon!"
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

            CreatePart(PrimitiveType.Capsule, "Coat", npc.transform, new Vector3(0f, 0.6f, 0f), new Vector3(0.55f, 0.6f, 0.55f), coatMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cylinder, "Scarf", npc.transform, new Vector3(0f, 1.27f, 0f), new Vector3(0.34f, 0.04f, 0.34f), scarfMat, Quaternion.identity);
            CreatePart(PrimitiveType.Sphere, "Head", npc.transform, new Vector3(0f, 1.43f, 0f), Vector3.one * 0.26f, skinMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cylinder, "Hat_Brim", npc.transform, new Vector3(0f, 1.55f, 0f), new Vector3(0.5f, 0.012f, 0.5f), hatMat, Quaternion.identity);
            CreatePart(PrimitiveType.Cylinder, "Hat_Crown", npc.transform, new Vector3(0f, 1.65f, 0f), new Vector3(0.2f, 0.1f, 0.2f), hatMat, Quaternion.identity);

            var component = npc.AddComponent<Npc>();
            var so = new SerializedObject(component);
            so.FindProperty("definition").objectReferenceValue = definition;
            so.FindProperty("dialogueUI").objectReferenceValue = dialogueUi;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Tablón de corcho en el centro de la pared del fondo + panel con la colección de cultivos y variantes.</summary>
        static void BuildCollectionBoard(Transform hud, Transform gallery, GameObject player, GameObject rig, Material woodMat)
        {
            var corkMat = GetOrCreateMaterial("M_Gallery_Board", new Color(0.72f, 0.52f, 0.32f));

            var ui = BuildListPanel(hud, "CollectionUI", "Collection", new Vector2(760f, 640f));
            var collectionUi = ui.Root.AddComponent<CollectionUI>();
            var uiSo = new SerializedObject(collectionUi);
            SetModalPanelRefs(uiSo, ui, player, rig);
            uiSo.FindProperty("messageLabel").objectReferenceValue = ui.Message;
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
        static void BuildCropPicker(Transform hud, GameObject player, GameObject rig)
        {
            var ui = BuildListPanel(hud, "CropPickerUI", "What will you paint?", new Vector2(760f, 560f));
            Object.DestroyImmediate(ui.Message.gameObject);
            var so = new SerializedObject(ui.Root.AddComponent<CropPickerUI>());
            SetModalPanelRefs(so, ui, player, rig);
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static string BrushDescription(BrushKind kind) => kind switch
        {
            BrushKind.Fill => "Click a zone of the sketch to fill it in one go.",
            BrushKind.Glaze => "A see-through layer that mixes with the colors below.",
            _ => "A new brush for your palette."
        };

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
            so.FindProperty("artistLevel").objectReferenceValue = player.GetComponent<ArtistLevel>();
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
