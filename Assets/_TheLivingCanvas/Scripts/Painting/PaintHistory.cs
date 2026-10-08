using System;
using System.Collections.Generic;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Undo/redo por instantáneas completas de la pintura (una por trazo).
    /// Reutiliza los buffers para no generar basura mientras se pinta.
    /// </summary>
    public class PaintHistory
    {
        readonly int capacity;
        readonly LinkedList<Color32[]> undo = new();
        readonly Stack<Color32[]> redo = new();
        readonly Stack<Color32[]> pool = new();

        public PaintHistory(int capacity) => this.capacity = Mathf.Max(1, capacity);

        public bool CanUndo => undo.Count > 0;
        public bool CanRedo => redo.Count > 0;

        /// <summary>Guarda el estado actual antes de modificarlo. Invalida el redo.</summary>
        public void Record(Color32[] current)
        {
            PushUndo(Copy(current));
            while (redo.Count > 0)
                pool.Push(redo.Pop());
        }

        public bool Undo(Color32[] current)
        {
            if (!CanUndo) return false;
            var previous = undo.Last.Value;
            undo.RemoveLast();
            redo.Push(Copy(current));
            Array.Copy(previous, current, current.Length);
            pool.Push(previous);
            return true;
        }

        public bool Redo(Color32[] current)
        {
            if (!CanRedo) return false;
            var next = redo.Pop();
            PushUndo(Copy(current));
            Array.Copy(next, current, current.Length);
            pool.Push(next);
            return true;
        }

        void PushUndo(Color32[] snapshot)
        {
            undo.AddLast(snapshot);
            if (undo.Count <= capacity) return;
            pool.Push(undo.First.Value);
            undo.RemoveFirst();
        }

        Color32[] Copy(Color32[] source)
        {
            var buffer = pool.Count > 0 ? pool.Pop() : new Color32[source.Length];
            Array.Copy(source, buffer, source.Length);
            return buffer;
        }
    }
}
