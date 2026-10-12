using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Data;
using TheLivingCanvas.Save;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>Cultivos y estilos que el jugador sabe pintar. Se empieza con el girasol y sin estilos; el resto se compra en la tienda.</summary>
    public class Sketchbook : MonoBehaviour, ISaveable
    {
        [SerializeField] List<CropDefinition> knownCrops = new();
        [SerializeField] List<StyleDefinition> knownStyles = new();

        public IReadOnlyList<CropDefinition> KnownCrops => knownCrops;
        /// <summary>Estilos comprados (el estilo "Classic" no cuenta: siempre se puede elegir).</summary>
        public IReadOnlyList<StyleDefinition> KnownStyles => knownStyles;

        public bool Knows(CropDefinition crop) => knownCrops.Contains(crop);

        /// <summary>Aprende un cultivo nuevo (false si ya lo sabía).</summary>
        public bool Learn(CropDefinition crop)
        {
            if (crop == null || knownCrops.Contains(crop)) return false;
            knownCrops.Add(crop);
            return true;
        }

        public bool KnowsStyle(StyleDefinition style) => knownStyles.Contains(style);

        /// <summary>Aprende un estilo nuevo (false si ya lo sabía).</summary>
        public bool LearnStyle(StyleDefinition style)
        {
            if (style == null || knownStyles.Contains(style)) return false;
            knownStyles.Add(style);
            return true;
        }

        public void WriteSave(SaveData data)
        {
            data.knownCrops = knownCrops.Select(c => c.Id).ToList();
            data.knownStyles = knownStyles.Select(s => s.Id).ToList();
        }

        /// <summary>La lista guardada sustituye a la inicial.</summary>
        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            knownCrops.Clear();
            foreach (var id in data.knownCrops)
                if (registry.FindCrop(id) is { } crop) knownCrops.Add(crop);
            knownStyles.Clear();
            foreach (var id in data.knownStyles)
                if (registry.FindStyle(id) is { } style) knownStyles.Add(style);
        }
    }
}
