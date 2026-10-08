using System.Linq;
using TheLivingCanvas.Core;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Player;
using Unity.Cinemachine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.InputSystem;
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

        [MenuItem("TheLivingCanvas/Build Studio Scene")]
        public static void Build()
        {
            if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
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
            BuildCameraRig(player);
            BuildHud(player.GetComponent<PlayerInteractor>());
            BuildTestLamp(environment.transform, new Vector3(-4.5f, 0.8f, 4.2f));

            var volumeGo = new GameObject("Global Volume");
            var volume = volumeGo.AddComponent<Volume>();
            volume.isGlobal = true;
            volume.sharedProfile = CreateVolumeProfile();

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets();
            Debug.Log($"[StudioSceneBuilder] Escena generada en {ScenePath}");
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

        static void BuildCameraRig(GameObject player)
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

            var modeController = rig.AddComponent<CameraModeController>();
            var so = new SerializedObject(modeController);
            so.FindProperty("thirdPersonCamera").objectReferenceValue = tp;
            so.FindProperty("firstPersonCamera").objectReferenceValue = fp;
            so.FindProperty("playerMovement").objectReferenceValue = player.GetComponent<PlayerMovement>();
            so.FindProperty("playerVisuals").objectReferenceValue = player.transform.Find("Visuals").gameObject;
            so.FindProperty("debugToggleAction").objectReferenceValue = GetAction("Player/ToggleView");
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>HUD provisional: aviso de interacción abajo al centro.</summary>
        static void BuildHud(PlayerInteractor interactor)
        {
            var hud = new GameObject("HUD");
            hud.AddComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = hud.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.matchWidthOrHeight = 0.5f;

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
