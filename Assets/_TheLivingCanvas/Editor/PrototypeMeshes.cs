using System.Collections.Generic;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Mallas procedurales del prototipo artístico, con UVs pensadas para pintar encima:
    ///  - Box: UV en metros (1 tile = N m) y vértices con irregularidad artesanal; la veta va en el eje largo.
    ///  - Blade: hoja/pétalo con la silueta en el UV (la plantilla de Krita muestra esa silueta).
    ///  - Lathe / Tube: maceta y tallo.
    /// Las constantes de silueta (a, b, L, HALF) deben coincidir con Tools/make_prototype_textures.py.
    /// </summary>
    public static class PrototypeMeshes
    {
        public const float LeafL = 0.22f, LeafHalf = 0.050f, LeafA = 0.70f, LeafB = 0.80f;
        public const float PetalL = 0.16f, PetalHalf = 0.034f, PetalA = 0.90f, PetalB = 0.60f;

        // Caras: 4 índices de esquina; el orden se corrige solo para que mire hacia fuera.
        static readonly int[][] BoxFaces =
        {
            new[] { 1, 3, 7, 5 }, new[] { 0, 4, 6, 2 },
            new[] { 2, 3, 7, 6 }, new[] { 0, 1, 5, 4 },
            new[] { 4, 5, 7, 6 }, new[] { 0, 2, 3, 1 },
        };
        // Ejes de UV (p, q) por cara.
        static readonly int[][] BoxUvAxes =
        {
            new[] { 2, 1 }, new[] { 2, 1 }, new[] { 0, 2 }, new[] { 0, 2 }, new[] { 0, 1 }, new[] { 0, 1 },
        };

        /// <param name="tile">metros por repetición de la textura</param>
        /// <param name="grainAxis">eje (0 x, 1 y, 2 z) a lo largo del cual va la veta; -1 = sin veta</param>
        /// <param name="jitter">irregularidad de las esquinas en metros</param>
        public static Mesh Box(string name, Vector3 size, float tile, int grainAxis, int seed, float jitter = 0.006f)
        {
            var rng = new System.Random(seed);
            var h = size * 0.5f;
            var corners = new Vector3[8];
            for (var i = 0; i < 8; i++)
            {
                var c = new Vector3((i & 1) == 0 ? -h.x : h.x, (i & 2) == 0 ? -h.y : h.y, (i & 4) == 0 ? -h.z : h.z);
                corners[i] = c + new Vector3(R(rng), R(rng), R(rng)) * jitter;
            }

            var uvOffset = new Vector2((float)rng.NextDouble(), (float)rng.NextDouble());
            var verts = new List<Vector3>();
            var norms = new List<Vector3>();
            var uvs = new List<Vector2>();
            var tris = new List<int>();

            for (var f = 0; f < 6; f++)
            {
                var idx = (int[])BoxFaces[f].Clone();
                var a = corners[idx[0]]; var b = corners[idx[1]]; var c = corners[idx[2]];
                var center = (corners[idx[0]] + corners[idx[1]] + corners[idx[2]] + corners[idx[3]]) * 0.25f;
                var n = Vector3.Cross(b - a, c - a).normalized;
                if (Vector3.Dot(n, center) < 0f) // mirando hacia dentro: invertir el orden
                {
                    System.Array.Reverse(idx);
                    n = -n;
                }
                var p = BoxUvAxes[f][0]; var q = BoxUvAxes[f][1];
                var start = verts.Count;
                foreach (var ci in idx)
                {
                    var pos = corners[ci];
                    var uv = new Vector2(pos[p], pos[q]) / tile;
                    if (grainAxis == p) uv = new Vector2(pos[q], pos[p]) / tile; // la veta (v) va a lo largo del eje largo
                    verts.Add(pos); norms.Add(n); uvs.Add(uv + uvOffset);
                }
                tris.AddRange(new[] { start, start + 1, start + 2, start, start + 2, start + 3 });
            }

            return Make(name, verts, norms, uvs, tris);
        }

        public static Mesh Quad(string name, float w, float h)
        {
            var verts = new List<Vector3>
            {
                new Vector3(-w / 2, -h / 2, 0), new Vector3(-w / 2, h / 2, 0),
                new Vector3(w / 2, h / 2, 0), new Vector3(w / 2, -h / 2, 0),
            };
            var norms = new List<Vector3> { Vector3.back, Vector3.back, Vector3.back, Vector3.back };
            var uvs = new List<Vector2> { new Vector2(0, 0), new Vector2(0, 1), new Vector2(1, 1), new Vector2(1, 0) };
            return Make(name, verts, norms, uvs, new List<int> { 0, 1, 2, 0, 2, 3 });
        }

        /// <summary>Superficie de revolución. profile = (radio, y) de abajo-centro, por fuera, hasta dentro.</summary>
        public static Mesh Lathe(string name, Vector2[] profile, int segments, float uvTile)
        {
            var verts = new List<Vector3>(); var norms = new List<Vector3>(); var uvs = new List<Vector2>(); var tris = new List<int>();
            var n = profile.Length;
            var along = new float[n];
            for (var i = 1; i < n; i++) along[i] = along[i - 1] + (profile[i] - profile[i - 1]).magnitude;

            for (var i = 0; i < n; i++)
            {
                var prev = profile[Mathf.Max(i - 1, 0)]; var next = profile[Mathf.Min(i + 1, n - 1)];
                var t = (next - prev).normalized;
                var nr = new Vector2(t.y, -t.x); // normal en el plano (radio, y)
                for (var s = 0; s <= segments; s++)
                {
                    var ang = s / (float)segments * Mathf.PI * 2f;
                    var dir = new Vector3(Mathf.Cos(ang), 0f, Mathf.Sin(ang));
                    verts.Add(dir * profile[i].x + Vector3.up * profile[i].y);
                    norms.Add((dir * nr.x + Vector3.up * nr.y).normalized);
                    uvs.Add(new Vector2(s / (float)segments, along[i] / uvTile));
                }
            }
            var stride = segments + 1;
            for (var i = 0; i < n - 1; i++)
                for (var s = 0; s < segments; s++)
                {
                    var a = i * stride + s; var b = a + 1; var c = a + stride; var d = c + 1;
                    tris.AddRange(new[] { a, b, c, b, d, c });
                }
            var mesh = Make(name, verts, norms, uvs, tris);
            FixWinding(mesh);
            return mesh;
        }

        /// <summary>Tubo a lo largo de una curva (en el plano Y-Z). U = alrededor, V = a lo largo.</summary>
        public static Mesh Tube(string name, System.Func<float, Vector3> curve, float r0, float r1, int rings, int sides)
        {
            var verts = new List<Vector3>(); var norms = new List<Vector3>(); var uvs = new List<Vector2>(); var tris = new List<int>();
            for (var i = 0; i <= rings; i++)
            {
                var t = i / (float)rings;
                var p = curve(t);
                var tan = (curve(Mathf.Min(t + 0.01f, 1f)) - curve(Mathf.Max(t - 0.01f, 0f))).normalized;
                var nrm = Vector3.Cross(tan, Vector3.right).normalized;
                var bin = Vector3.Cross(tan, nrm);
                var r = Mathf.Lerp(r0, r1, t);
                for (var s = 0; s <= sides; s++)
                {
                    var a = s / (float)sides * Mathf.PI * 2f;
                    var dir = nrm * Mathf.Cos(a) + bin * Mathf.Sin(a);
                    verts.Add(p + dir * r); norms.Add(dir); uvs.Add(new Vector2(s / (float)sides, t));
                }
            }
            var stride = sides + 1;
            for (var i = 0; i < rings; i++)
                for (var s = 0; s < sides; s++)
                {
                    var a = i * stride + s; var b = a + 1; var c = a + stride; var d = c + 1;
                    tris.AddRange(new[] { a, b, c, b, d, c });
                }
            var mesh = Make(name, verts, norms, uvs, tris);
            FixWinding(mesh);
            return mesh;
        }

        /// <summary>
        /// Hoja o pétalo: tira con silueta semiancho(v) = half * sin(pi * v^a)^b, base en el origen apuntando a +Y.
        /// curl &gt; 0 curva la punta hacia +Z (la cara frontal es +Z), cup &gt; 0 encorva los bordes hacia +Z.
        /// El UV x = 0.5 + x / (L/2) para que la silueta se vea tal cual en la textura 1:2.
        /// </summary>
        public static Mesh Blade(string name, float L, float half, float a, float b, float curl, float cup, int rows = 16, int cols = 7)
        {
            var verts = new List<Vector3>(); var uvs = new List<Vector2>(); var tris = new List<int>();
            var spine = Vector3.zero;
            for (var i = 0; i <= rows; i++)
            {
                var v = i / (float)rows;
                var phi = curl * v * Mathf.Sqrt(v);
                if (i > 0)
                {
                    var vm = (i - 0.5f) / rows;
                    var phim = curl * vm * Mathf.Sqrt(vm);
                    spine += new Vector3(0f, Mathf.Cos(phim), Mathf.Sin(phim)) * (L / rows);
                }
                var hw = half * Mathf.Pow(Mathf.Max(0f, Mathf.Sin(Mathf.PI * Mathf.Pow(v, a))), b);
                var nrm = new Vector3(0f, -Mathf.Sin(phi), Mathf.Cos(phi));
                for (var j = 0; j < cols; j++)
                {
                    var t = j / (float)(cols - 1) * 2f - 1f;
                    var x = t * hw;
                    verts.Add(spine + new Vector3(x, 0f, 0f) + nrm * (cup * x * x / half));
                    uvs.Add(new Vector2(0.5f + x / (L / 2f), v));
                }
            }
            for (var i = 0; i < rows; i++)
                for (var j = 0; j < cols - 1; j++)
                {
                    var p0 = i * cols + j; var p1 = p0 + 1; var p2 = p0 + cols; var p3 = p2 + 1;
                    tris.AddRange(new[] { p0, p2, p1, p1, p2, p3 });
                }
            var mesh = new Mesh { name = name };
            mesh.SetVertices(verts); mesh.SetUVs(0, uvs); mesh.SetTriangles(tris, 0);
            mesh.RecalculateNormals();
            // La cara frontal debe ser la +Z (la que se curva hacia dentro): si no, se invierte el orden.
            var mid = (rows / 2) * cols + cols / 2;
            if (mesh.normals[mid].z < 0f) { tris.Reverse(); mesh.SetTriangles(tris, 0); mesh.RecalculateNormals(); }
            mesh.RecalculateBounds();
            return mesh;
        }

        static void FixWinding(Mesh mesh)
        {
            // Que el triángulo apunte hacia donde dice la normal del vértice.
            var v = mesh.vertices; var n = mesh.normals; var t = mesh.triangles;
            for (var i = 0; i < t.Length; i += 3)
            {
                var fn = Vector3.Cross(v[t[i + 1]] - v[t[i]], v[t[i + 2]] - v[t[i]]);
                if (fn.sqrMagnitude < 1e-12f) continue;
                if (Vector3.Dot(fn, n[t[i]] + n[t[i + 1]] + n[t[i + 2]]) < 0f)
                    (t[i + 1], t[i + 2]) = (t[i + 2], t[i + 1]);
            }
            mesh.triangles = t;
        }

        static Mesh Make(string name, List<Vector3> v, List<Vector3> n, List<Vector2> uv, List<int> tris)
        {
            var mesh = new Mesh { name = name };
            mesh.SetVertices(v); mesh.SetNormals(n); mesh.SetUVs(0, uv); mesh.SetTriangles(tris, 0);
            mesh.RecalculateBounds();
            return mesh;
        }

        static float R(System.Random rng) => (float)(rng.NextDouble() * 2.0 - 1.0);
    }
}
