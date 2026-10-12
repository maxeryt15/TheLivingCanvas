using System;
using TheLivingCanvas.Data;
using UnityEngine;
using Object = UnityEngine.Object;

namespace TheLivingCanvas.Save
{
    /// <summary>Todos los assets de datos del juego, para volver de un id guardado al asset. La rellena el builder de la escena.</summary>
    [Serializable]
    public class SaveRegistry
    {
        [SerializeField] CropDefinition[] crops = Array.Empty<CropDefinition>();
        [SerializeField] PigmentDefinition[] pigments = Array.Empty<PigmentDefinition>();
        [SerializeField] BrushDefinition[] brushes = Array.Empty<BrushDefinition>();
        [SerializeField] StyleDefinition[] styles = Array.Empty<StyleDefinition>();
        [SerializeField] CanvasType[] canvasTypes = Array.Empty<CanvasType>();
        [SerializeField] CollectionSet[] sets = Array.Empty<CollectionSet>();

        // Cada Find avisa y devuelve null con un id desconocido (ej. un asset quitado tras guardar).
        public CropDefinition FindCrop(string id) => Find(crops, id, c => c.Id);
        public PigmentDefinition FindPigment(string id) => Find(pigments, id, p => p.Id);
        public BrushDefinition FindBrush(string id) => Find(brushes, id, b => b.Id);
        public StyleDefinition FindStyle(string id) => Find(styles, id, s => s.Id);
        public CanvasType FindCanvasType(string id) => Find(canvasTypes, id, c => c.Id);
        public CollectionSet FindSet(string id) => Find(sets, id, s => s.Id);

        static T Find<T>(T[] items, string id, Func<T, string> getId) where T : Object
        {
            foreach (var item in items)
                if (item != null && getId(item) == id) return item;
            Debug.LogWarning($"[Save] Unknown {typeof(T).Name} id '{id}' in save; skipped.");
            return null;
        }
    }
}
