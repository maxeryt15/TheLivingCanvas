using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Genera Museum.unity a partir de los FBX exportados desde Blender (Art/Models/Museum) y de los JSON de luces.
    /// Es independiente de Studio.unity y del resto de builders. Idempotente: se puede volver a ejecutar.
    /// Menu: TheLivingCanvas/Build Museum Scene.
    /// </summary>
    public static class MuseumSceneBuilder
    {
        const string Root = "Assets/_TheLivingCanvas";
        const string ModelFolder = Root + "/Art/Models/Museum";
        const string ScenePath = Root + "/Scenes/Museum.unity";
        const string VolumeProfilePath = Root + "/Settings/StudioVolumeProfile.asset";
        const string PlayerPrefabPath = Root + "/Prefabs/Player/Player.prefab";
        // true: el jugador empieza fuera, frente a la puerta principal; false: dentro del Hall (marcador PlayerStart)
        const bool StartOutside = true;
        const float ExteriorStartZ = 10.5f;
        const float InteriorOffsetY = -60f;   // el interior vive 60 m bajo el exterior (AreaTransition activa solo uno)

        const StaticEditorFlags StaticAll = StaticEditorFlags.ContributeGI | StaticEditorFlags.BatchingStatic
            | StaticEditorFlags.OccluderStatic | StaticEditorFlags.OccludeeStatic | StaticEditorFlags.ReflectionProbeStatic;
        const StaticEditorFlags StaticVegetation = StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccludeeStatic;

        // FBX interiores que reciben MeshCollider (el resto de Int_ no: marcadores y demas)
        static readonly string[] InteriorColliderFiles =
        {
            "Museum_Int_Structure", "Museum_Int_Wall_Finish", "Museum_Int_Exhibition_Rooms", "Museum_Int_Furniture",
            "Museum_Int_Service_Areas", "Museum_Int_Utilities", "Museum_Int_Doors_Windows",
        };
        static readonly string[] ExteriorColliderFiles = { "Museum_Ext_Architecture", "Museum_Ext_Ground", "Museum_Ext_Props" };
        // Nombres (contiene) que no reciben collider en el interior
        static readonly string[] ColliderSkip = { "Curtain", "Glass", "Plant", "Int_Wing_Tracks", "Int_Ceiling_Features", "Hatch_Pit", "Door_" };

        [Serializable]
        class LightEntry
        {
            public string name;
            public string type;
            public float energy;
            public float[] color;
            public float radius;
            public float spot_size_deg;
            public float spot_blend;
            public float[] size;
        }

        [Serializable]
        class LightFile
        {
            public LightEntry[] lights;
        }

        static int _objects, _colliders, _lights;

        [MenuItem("TheLivingCanvas/Build Museum Scene")]
        public static void Build()
        {
            if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;

            _objects = _colliders = _lights = 0;
            EnsureFolder(Root + "/Scenes");

            ConfigureImporters();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var exterior = new GameObject("Museum_Exterior").transform;
            exterior.position = Vector3.zero;
            var interior = new GameObject("Museum_Interior").transform;
            interior.position = new Vector3(0f, InteriorOffsetY, 0f);   // bajo el mapa: solo esta activa el area donde esta el jugador

            // Modelos
            var extInstances = new List<GameObject>();
            var intInstances = new List<GameObject>();
            foreach (var path in Directory.GetFiles(ModelFolder, "*.fbx"))
            {
                var assetPath = path.Replace('\\', '/');
                var fileName = Path.GetFileNameWithoutExtension(assetPath);
                bool isInterior = fileName.StartsWith("Museum_Int_");
                bool isExterior = fileName.StartsWith("Museum_Ext_");
                if (!isInterior && !isExterior) continue;

                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
                if (prefab == null) { Debug.LogWarning("No se pudo cargar " + assetPath); continue; }
                var instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
                instance.name = fileName;
                instance.transform.SetParent(isInterior ? interior : exterior, false);
                instance.transform.localPosition = Vector3.zero;
                (isInterior ? intInstances : extInstances).Add(instance);
            }

            foreach (var inst in intInstances) ApplyStatic(inst);
            foreach (var inst in extInstances) ApplyStatic(inst);

            // Colliders
            foreach (var inst in intInstances)
                if (Array.IndexOf(InteriorColliderFiles, inst.name) >= 0) AddColliders(inst, true);
            foreach (var inst in extInstances)
                if (Array.IndexOf(ExteriorColliderFiles, inst.name) >= 0) AddColliders(inst, false);

            BuildInteriorBlocker(exterior);

            // Luces
            var intLights = BuildLights(interior, "Museum_Int_Lights.json", intInstances, false);
            var extHasSun = BuildLights(exterior, "Museum_Ext_Lights.json", extInstances, true);
            if (!extHasSun) AddFallbackSun(exterior);
            _ = intLights;

            BuildEnvironment();
            BuildPlayer(exterior, interior, intInstances);

            EditorSceneManager.SaveScene(scene, ScenePath);
            AssetDatabase.SaveAssets();
            Debug.Log($"Museum generada: {ScenePath} | objetos {_objects}, colliders {_colliders}, luces {_lights}, bloqueador interior");
        }

        // ---------------------------------------------------------------- bloqueador interior
        // El exterior es una cascara hueca: por rendijas finas (hueco entre hojas de la puerta, juntas de marco y cristal)
        // se veria el cielo a traves del interior vacio. Una caja oscura cerrada justo dentro de los muros hace que
        // cualquier rendija muestre oscuridad calida. 12 triangulos, sin sombras y sin collider.
        static void BuildInteriorBlocker(Transform exterior)
        {
            const string matFolder = Root + "/Art/Materials/Museum";
            const string matPath = matFolder + "/M_Ext_InteriorBlocker.mat";
            const string meshFolder = ModelFolder + "/Generated";
            const string meshPath = meshFolder + "/ExteriorInteriorBlocker.asset";

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) { Debug.LogError("No se encontro el shader Universal Render Pipeline/Lit: sin bloqueador interior."); return; }

            EnsureFolder(matFolder);
            var color = new Color(0.085f, 0.07f, 0.06f);
            var mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
            if (mat == null)
            {
                mat = new Material(shader);
                AssetDatabase.CreateAsset(mat, matPath);
            }
            mat.SetColor("_BaseColor", color);
            mat.SetFloat("_Smoothness", 0f);
            mat.SetFloat("_Metallic", 0f);
            EditorUtility.SetDirty(mat);

            // Caja con caras planas (vertices separados por cara), normales hacia fuera
            Vector3 min = new Vector3(-7.55f, 0.1f, -5.55f), max = new Vector3(7.55f, 8.05f, 5.55f);
            var verts = new List<Vector3>();
            var norms = new List<Vector3>();
            var uvs = new List<Vector2>();
            var tris = new List<int>();
            // Cada cara: 4 esquinas en sentido antihorario visto desde fuera (Unity usa horario como frontal => orden horario desde fuera)
            void Face(Vector3 normal, Vector3 a, Vector3 b, Vector3 c, Vector3 d)
            {
                int i = verts.Count;
                verts.Add(a); verts.Add(b); verts.Add(c); verts.Add(d);
                for (int k = 0; k < 4; k++) norms.Add(normal);
                uvs.Add(new Vector2(0, 0)); uvs.Add(new Vector2(0, 1)); uvs.Add(new Vector2(1, 1)); uvs.Add(new Vector2(1, 0));
                // a,b,c,d en sentido horario visto desde fuera
                tris.Add(i); tris.Add(i + 1); tris.Add(i + 2);
                tris.Add(i); tris.Add(i + 2); tris.Add(i + 3);
            }
            float x0 = min.x, x1 = max.x, y0 = min.y, y1 = max.y, z0 = min.z, z1 = max.z;
            Face(Vector3.right,   new Vector3(x1, y0, z0), new Vector3(x1, y1, z0), new Vector3(x1, y1, z1), new Vector3(x1, y0, z1));
            Face(Vector3.left,    new Vector3(x0, y0, z1), new Vector3(x0, y1, z1), new Vector3(x0, y1, z0), new Vector3(x0, y0, z0));
            Face(Vector3.up,      new Vector3(x0, y1, z0), new Vector3(x0, y1, z1), new Vector3(x1, y1, z1), new Vector3(x1, y1, z0));
            Face(Vector3.down,    new Vector3(x0, y0, z1), new Vector3(x0, y0, z0), new Vector3(x1, y0, z0), new Vector3(x1, y0, z1));
            Face(Vector3.forward, new Vector3(x1, y0, z1), new Vector3(x1, y1, z1), new Vector3(x0, y1, z1), new Vector3(x0, y0, z1));
            Face(Vector3.back,    new Vector3(x0, y0, z0), new Vector3(x0, y1, z0), new Vector3(x1, y1, z0), new Vector3(x1, y0, z0));

            EnsureFolder(meshFolder);
            var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);
            bool isNew = mesh == null;
            if (isNew) mesh = new Mesh { name = "ExteriorInteriorBlocker" };
            else mesh.Clear();
            mesh.SetVertices(verts);
            mesh.SetNormals(norms);
            mesh.SetUVs(0, uvs);
            mesh.SetTriangles(tris, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            if (isNew) AssetDatabase.CreateAsset(mesh, meshPath);
            else EditorUtility.SetDirty(mesh);

            var go = new GameObject("Exterior_InteriorBlocker");
            go.transform.SetParent(exterior, false);
            go.transform.localPosition = Vector3.zero;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = mat;
            mr.shadowCastingMode = ShadowCastingMode.Off;
            mr.receiveShadows = false;
            GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccludeeStatic);
            _objects++;
        }

        // ---------------------------------------------------------------- importadores
        static void ConfigureImporters()
        {
            foreach (var path in Directory.GetFiles(ModelFolder, "*.fbx"))
            {
                var assetPath = path.Replace('\\', '/');
                if (AssetImporter.GetAtPath(assetPath) is not ModelImporter imp) continue;

                var name = Path.GetFileNameWithoutExtension(assetPath);
                bool lightmapUv = !name.EndsWith("_Vegetation") && !name.EndsWith("_Unity_Markers");
                bool changed = false;

                changed |= Set(imp.globalScale, 1f, () => imp.globalScale = 1f);
                changed |= Set(imp.useFileScale, true, () => imp.useFileScale = true);
                changed |= Set(imp.importCameras, false, () => imp.importCameras = false);
                changed |= Set(imp.importLights, false, () => imp.importLights = false);
                changed |= Set(imp.importBlendShapes, false, () => imp.importBlendShapes = false);
                changed |= Set(imp.importAnimation, false, () => imp.importAnimation = false);
                changed |= Set(imp.animationType, ModelImporterAnimationType.None, () => imp.animationType = ModelImporterAnimationType.None);
                changed |= Set(imp.isReadable, false, () => imp.isReadable = false);
                changed |= Set(imp.meshCompression, ModelImporterMeshCompression.Off, () => imp.meshCompression = ModelImporterMeshCompression.Off);
                changed |= Set(imp.materialImportMode, ModelImporterMaterialImportMode.ImportViaMaterialDescription,
                    () => imp.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription);
                changed |= Set(imp.generateSecondaryUV, lightmapUv, () => imp.generateSecondaryUV = lightmapUv);
                changed |= Set(imp.weldVertices, true, () => imp.weldVertices = true);

                if (changed) imp.SaveAndReimport();
            }
        }

        // Aplica el cambio solo si el valor actual difiere; devuelve true si cambio algo
        static bool Set<T>(T current, T wanted, Action apply)
        {
            if (EqualityComparer<T>.Default.Equals(current, wanted)) return false;
            apply();
            return true;
        }

        // ---------------------------------------------------------------- estaticos y colliders
        static bool IsAnimated(Transform t, Transform stopAt)
        {
            for (var c = t; c != null && c != stopAt; c = c.parent)
                if (c.name.StartsWith("Door_") || c.name.StartsWith("Hatch_Lid")) return true;
            return false;
        }

        static void ApplyStatic(GameObject instance)
        {
            bool vegetation = instance.name.EndsWith("_Vegetation");
            bool markers = instance.name.EndsWith("_Unity_Markers");
            foreach (var t in instance.GetComponentsInChildren<Transform>(true))
            {
                _objects++;
                if (markers) continue;
                if (IsAnimated(t, instance.transform.parent)) continue;
                GameObjectUtility.SetStaticEditorFlags(t.gameObject, vegetation ? StaticVegetation : StaticAll);
            }
        }

        static void AddColliders(GameObject instance, bool applySkip)
        {
            foreach (var mr in instance.GetComponentsInChildren<MeshRenderer>(true))
            {
                var mf = mr.GetComponent<MeshFilter>();
                if (mf == null || mf.sharedMesh == null) continue;
                if (applySkip && ShouldSkipCollider(mr.transform, instance.transform)) continue;
                if (mr.GetComponent<Collider>() != null) continue;
                var mc = mr.gameObject.AddComponent<MeshCollider>();
                mc.sharedMesh = mf.sharedMesh;
                mc.convex = false;
                _colliders++;
            }
        }

        static bool ShouldSkipCollider(Transform t, Transform stopAt)
        {
            for (var c = t; c != null && c != stopAt; c = c.parent)
                foreach (var token in ColliderSkip)
                    if (c.name.Contains(token)) return true;
            return false;
        }

        // ---------------------------------------------------------------- luces
        // Devuelve true si se creo una luz Directional desde el JSON (sol)
        static bool BuildLights(Transform root, string jsonName, List<GameObject> instances, bool exterior)
        {
            var jsonPath = $"{ModelFolder}/{jsonName}";
            if (!File.Exists(jsonPath)) { Debug.LogWarning("Falta " + jsonPath); return false; }
            var file = JsonUtility.FromJson<LightFile>(File.ReadAllText(jsonPath));
            if (file == null || file.lights == null) return false;

            // Indice de marcadores del FBX *_Unity_Markers
            var markers = new Dictionary<string, Transform>();
            var markerList = new List<Transform>();
            foreach (var inst in instances)
            {
                if (!inst.name.EndsWith("_Unity_Markers")) continue;
                foreach (var t in inst.GetComponentsInChildren<Transform>(true))
                {
                    if (!markers.ContainsKey(t.name)) markers[t.name] = t;
                    markerList.Add(t);
                }
            }

            var lightsRoot = new GameObject("Lights").transform;
            lightsRoot.SetParent(root, false);

            bool sun = false;
            foreach (var e in file.lights)
            {
                if (string.IsNullOrEmpty(e.name)) continue;
                var type = (e.type ?? "POINT").ToUpperInvariant();
                if (type == "AREA" && e.name.Contains("Bounce")) continue;

                var marker = FindMarker(markers, markerList, e.name, false);
                if (marker == null) { Debug.LogWarning("Sin marcador para la luz " + e.name); continue; }
                var target = type == "POINT" ? null : FindMarker(markers, markerList, e.name + "_Target", true);

                var go = new GameObject(e.name);
                go.transform.SetParent(lightsRoot, false);
                go.transform.position = marker.position;
                var light = go.AddComponent<Light>();
                light.color = ToColor(e.color);

                switch (type)
                {
                    case "SPOT":
                        light.type = LightType.Spot;
                        light.spotAngle = e.spot_size_deg;
                        light.innerSpotAngle = e.spot_size_deg * (1f - e.spot_blend);
                        light.range = 8f;
                        light.intensity = Mathf.Clamp(e.energy / 120f, 0.5f, 3f);
                        light.shadows = LightShadows.None;
                        Aim(go.transform, target, marker);
                        break;
                    case "AREA":
                        light.type = LightType.Point;
                        light.range = 14f;
                        light.intensity = 1.2f;
                        light.shadows = LightShadows.None;
                        break;
                    case "SUN":
                        light.type = LightType.Directional;
                        light.intensity = 1.2f;
                        light.shadows = LightShadows.Soft;
                        Aim(go.transform, target, marker);
                        RenderSettings.sun = light;
                        sun = true;
                        break;
                    default:
                        light.type = LightType.Point;
                        light.range = Mathf.Clamp(Mathf.Sqrt(e.energy) * 0.45f, 3f, 12f);
                        light.intensity = Mathf.Clamp(e.energy / 220f, 0.25f, 3f);
                        light.shadows = LightShadows.None;
                        break;
                }
                light.lightmapBakeType = LightmapBakeType.Mixed;
                _lights++;
            }
            return sun;
        }

        static void Aim(Transform lightTransform, Transform target, Transform marker)
        {
            if (target != null && (target.position - lightTransform.position).sqrMagnitude > 1e-6f)
                lightTransform.rotation = Quaternion.LookRotation((target.position - lightTransform.position).normalized);
            else
                lightTransform.rotation = marker.rotation; // sin target: se usa la orientacion del marcador
        }

        static Transform FindMarker(Dictionary<string, Transform> exact, List<Transform> all, string name, bool isTarget)
        {
            if (exact.TryGetValue(name, out var t)) return t;
            foreach (var c in all)
            {
                if (!c.name.StartsWith(name)) continue;
                // Evita que "Light_X" coincida con "Light_X_Target"
                if (!isTarget && c.name.EndsWith("_Target")) continue;
                return c;
            }
            return null;
        }

        static Color ToColor(float[] c)
            => c != null && c.Length >= 3 ? new Color(c[0], c[1], c[2]) : Color.white;

        static void AddFallbackSun(Transform root)
        {
            var go = new GameObject("Sun");
            go.transform.SetParent(root, false);
            go.transform.rotation = Quaternion.Euler(45f, -30f, 0f);
            var sun = go.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.96f, 0.88f);
            sun.intensity = 1.2f;
            sun.shadows = LightShadows.Soft;
            sun.lightmapBakeType = LightmapBakeType.Mixed;
            RenderSettings.sun = sun;
            _lights++;
        }

        // ---------------------------------------------------------------- entorno
        static void BuildEnvironment()
        {
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.62f, 0.68f, 0.78f);
            RenderSettings.ambientEquatorColor = new Color(0.55f, 0.52f, 0.47f);
            RenderSettings.ambientGroundColor = new Color(0.30f, 0.27f, 0.24f);
            RenderSettings.fog = false;

            var volGo = new GameObject("Global Volume");
            var vol = volGo.AddComponent<Volume>();
            vol.isGlobal = true;
            vol.priority = 0f;
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(VolumeProfilePath);
            if (profile != null) vol.sharedProfile = profile;
            else Debug.LogWarning("No existe " + VolumeProfilePath + ": Global Volume sin perfil.");
        }

        // ---------------------------------------------------------------- jugador
        static void BuildPlayer(Transform exterior, Transform interior, List<GameObject> intInstances)
        {
            Vector3 pos = interior.position + new Vector3(0f, 0f, 0f);
            Transform start = null, hall = null;
            foreach (var inst in intInstances)
            {
                if (!inst.name.EndsWith("_Unity_Markers")) continue;
                foreach (var t in inst.GetComponentsInChildren<Transform>(true))
                {
                    if (start == null && t.name.StartsWith("PlayerStart")) start = t;
                    if (hall == null && t.name == "Light_Hall") hall = t;
                }
            }
            if (hall == null) hall = interior.Find("Lights/Light_Hall");   // la luz ya creada en el sitio del marcador
            if (start == null) Debug.LogWarning("No hay marcador PlayerStart: el jugador se coloca en el origen del interior.");
            else pos = start.position;
            pos += Vector3.up * 0.05f;

            float yaw = 0f;
            if (hall != null)
            {
                var dir = hall.position - pos;
                dir.y = 0f;
                if (dir.sqrMagnitude > 1e-6f) yaw = Quaternion.LookRotation(dir.normalized).eulerAngles.y;
            }

            // Punto de salida al exterior: delante de la puerta principal (fachada en z = +6). El raycast solo puede
            // tocar el exterior: el interior esta 60 m mas abajo y el origen del rayo (y = 30) queda por encima.
            Physics.SyncTransforms();
            Vector3 outdoorPos;
            var probe = new Vector3(0f, 30f, ExteriorStartZ);
            if (Physics.Raycast(probe, Vector3.down, out var hit, 60f, ~0, QueryTriggerInteraction.Ignore))
                outdoorPos = hit.point + Vector3.up * 0.05f;
            else
                outdoorPos = new Vector3(0f, 0.05f, ExteriorStartZ);

            // Inicio por defecto: fuera, mirando a la fachada.
            if (StartOutside)
            {
                pos = outdoorPos;
                yaw = 180f;   // hacia -z: la puerta
            }

            // La camara va antes que el jugador: PlayerMovement/PlayerInteractor buscan Camera.main en Awake.
            // Igual que en Studio: camara real con CinemachineBrain + rig de primera persona (mirar con raton/stick).
            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            cam.nearClipPlane = 0.05f;
            camGo.AddComponent<AudioListener>();
            camGo.AddComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>().renderPostProcessing = true;
            camGo.AddComponent<Unity.Cinemachine.CinemachineBrain>();
            camGo.transform.SetPositionAndRotation(pos + Vector3.up * 1.6f, Quaternion.Euler(0f, yaw, 0f));

            var playerPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PlayerPrefabPath);
            if (playerPrefab == null) { Debug.LogWarning("Falta " + PlayerPrefabPath); return; }
            var player = (GameObject)PrefabUtility.InstantiatePrefab(playerPrefab);
            player.transform.SetPositionAndRotation(pos, Quaternion.Euler(0f, yaw, 0f));
            var rig = StudioSceneBuilder.BuildCameraRig(player);
            // La vista en primera persona la orienta el PanTilt (no la rotacion del jugador): mirar hacia el Hall al empezar
            var panTilt = rig.GetComponentInChildren<Unity.Cinemachine.CinemachinePanTilt>(true);
            if (panTilt != null) panTilt.PanAxis.Value = yaw;

            // HUD nuevo (mira, prompt "[E] ...", resumen, avisos): se construye solo al arrancar
            new GameObject("HUD", typeof(TheLivingCanvas.Ui.Hud));
            new GameObject("PauseScreen", typeof(TheLivingCanvas.Ui.PauseScreen)); // pausa con ajustes, Main Menu y Quit
            new GameObject("DialogueBox", typeof(TheLivingCanvas.Ui.DialogueBox)); // diálogos de los NPCs y subtítulos
            new GameObject("JournalScreen", typeof(TheLivingCanvas.Ui.JournalScreen)); // cuaderno: objetos, pigmentos, notas (I / Tab / Y)
            new GameObject("Notifications", typeof(TheLivingCanvas.Ui.Notifications)); // avisos arriba a la derecha
            new GameObject("ObjectiveTracker", typeof(TheLivingCanvas.Ui.ObjectiveTracker)); // objetivos arriba a la izquierda
            new GameObject("HudStatus", typeof(TheLivingCanvas.Ui.HudStatus)); // monedas, nivel y pigmentos abajo a la izquierda

            // Música: las piezas de Audio/Music en orden aleatorio, fundidas entre sí
            var musicGo = new GameObject("Music", typeof(TheLivingCanvas.Audio.MusicPlaylist));
            var musicSo = new SerializedObject(musicGo.GetComponent<TheLivingCanvas.Audio.MusicPlaylist>());
            var trackGuids = AssetDatabase.FindAssets("t:AudioClip", new[] { "Assets/_TheLivingCanvas/Audio/Music" });
            var tracksProp = musicSo.FindProperty("tracks");
            tracksProp.arraySize = trackGuids.Length;
            for (int i = 0; i < trackGuids.Length; i++)
                tracksProp.GetArrayElementAtIndex(i).objectReferenceValue = AssetDatabase.LoadAssetAtPath<AudioClip>(AssetDatabase.GUIDToAssetPath(trackGuids[i]));
            musicSo.ApplyModifiedPropertiesWithoutUndo();

            // Fundido a negro para las transiciones entre areas
            var fadeGo = new GameObject("AreaFade", typeof(Canvas), typeof(CanvasGroup));
            var fadeCanvas = fadeGo.GetComponent<Canvas>();
            fadeCanvas.renderMode = RenderMode.ScreenSpaceOverlay;
            fadeCanvas.sortingOrder = 100;
            var fadeGroup = fadeGo.GetComponent<CanvasGroup>();
            fadeGroup.alpha = 0f;
            fadeGroup.blocksRaycasts = false;
            fadeGroup.interactable = false;
            var imgGo = new GameObject("Black", typeof(RectTransform), typeof(UnityEngine.UI.Image));
            imgGo.transform.SetParent(fadeGo.transform, false);
            var imgRt = (RectTransform)imgGo.transform;
            imgRt.anchorMin = Vector2.zero;
            imgRt.anchorMax = Vector2.one;
            imgRt.offsetMin = imgRt.offsetMax = Vector2.zero;
            var img = imgGo.GetComponent<UnityEngine.UI.Image>();
            var inkFade = TheLivingCanvas.Ui.UITheme.Current.ink; // tinta muy oscura en vez de negro puro
            img.color = new Color(inkFade.r * .35f, inkFade.g * .35f, inkFade.b * .35f, 1f);
            img.raycastTarget = false;

            // Puntos de aparicion y puertas (se crean tras ApplyStatic/AddColliders: sin flags estaticos ni MeshCollider)
            var spawnInterior = new GameObject("Spawn_Interior_Hall").transform;
            spawnInterior.SetParent(interior, false);
            spawnInterior.localPosition = new Vector3(0f, 0.55f, 4.4f);
            spawnInterior.localRotation = Quaternion.Euler(0f, 180f, 0f);   // mirando al interior del hall (-z)
            var spawnExterior = new GameObject("Spawn_Exterior_Front").transform;
            spawnExterior.SetParent(exterior, false);
            spawnExterior.position = outdoorPos;
            spawnExterior.rotation = Quaternion.identity;                   // de espaldas al edificio

            var areas = new GameObject("MuseumAreas").AddComponent<TheLivingCanvas.Interaction.AreaTransition>();
            var areasSo = new SerializedObject(areas);
            areasSo.FindProperty("exteriorRoot").objectReferenceValue = exterior.gameObject;
            areasSo.FindProperty("interiorRoot").objectReferenceValue = interior.gameObject;
            areasSo.FindProperty("startInside").boolValue = !StartOutside;
            areasSo.FindProperty("fade").objectReferenceValue = fadeGroup;
            areasSo.FindProperty("player").objectReferenceValue = player.transform;
            areasSo.FindProperty("panTilt").objectReferenceValue = panTilt;
            areasSo.ApplyModifiedPropertiesWithoutUndo();

            BuildDoor("Door_Enter_Museum", exterior, new Vector3(0f, 2.0f, 6.1f) - exterior.position, new Vector3(2.4f, 3.0f, 0.4f),
                "Enter to the museum", true, spawnInterior, areas);
            BuildDoor("Door_Exit_Museum", interior, new Vector3(0f, 2.0f, 5.45f), new Vector3(2.4f, 3.0f, 0.3f),
                "Exit museum", false, spawnExterior, areas);

            Debug.Log($"Museum: jugador en {pos}, mirando yaw {yaw:0}; puertas Door_Enter_Museum / Door_Exit_Museum, interior en {interior.position}");
            _objects++;
        }

        // Puerta interactuable (trigger) que teletransporta entre areas
        static void BuildDoor(string name, Transform parent, Vector3 localPos, Vector3 size, string prompt,
            bool leadsInside, Transform destination, TheLivingCanvas.Interaction.AreaTransition areas)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            var box = go.AddComponent<BoxCollider>();
            box.isTrigger = true;
            box.size = size;
            var door = go.AddComponent<TheLivingCanvas.Interaction.AreaDoor>();
            var so = new SerializedObject(door);
            so.FindProperty("prompt").stringValue = prompt;
            so.FindProperty("destination").objectReferenceValue = destination;
            so.FindProperty("leadsInside").boolValue = leadsInside;
            so.FindProperty("transition").objectReferenceValue = areas;
            so.ApplyModifiedPropertiesWithoutUndo();
            _objects++;
        }

        // ---------------------------------------------------------------- utilidades
        static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            var parent = Path.GetDirectoryName(path).Replace('\\', '/');
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }
    }
}
