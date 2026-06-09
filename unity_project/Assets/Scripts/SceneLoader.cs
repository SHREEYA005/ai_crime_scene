using UnityEngine;
using System.IO;

public class SceneLoader : MonoBehaviour
{
    public GameObject defaultPrefab;
    public GameObject[] namedPrefabs;

    void Start()
    {
        string path = Path.Combine(Application.streamingAssetsPath, "scene_data.json");

        if (!File.Exists(path))
        {
            Debug.LogError("scene_data.json not found in StreamingAssets! Path: " + path);
            return;
        }

        SceneData data = JsonUtility.FromJson<SceneData>(File.ReadAllText(path));

        if (data == null || data.objects == null)
        {
            Debug.LogError("Failed to parse scene JSON");
            return;
        }

        Debug.Log("Loading scene: " + data.case_title + " with " + data.objects.Length + " objects");

        foreach (var obj in data.objects)
        {
            SpawnObject(obj);
        }
    }

    void SpawnObject(SceneObject obj)
    {
        GameObject prefab = FindPrefab(obj.prefab) ?? defaultPrefab;
        if (prefab == null)
        {
            Debug.LogWarning("No prefab for: " + obj.label);
            return;
        }

        Vector3 pos = new Vector3(obj.position.x, obj.position.y, obj.position.z);
        Quaternion rot = Quaternion.Euler(obj.rotation.x, obj.rotation.y, obj.rotation.z);
        GameObject instance = Instantiate(prefab, pos, rot);
        instance.name = obj.label + "_" + obj.id;

        // Color by type
        Renderer rend = instance.GetComponent<Renderer>();
        if (rend != null)
        {
            Material mat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            mat.color = obj.label.Contains("person") ? Color.red : Color.yellow;
            rend.material = mat;
        }

        AddLabel(instance, obj.label, obj.confidence);
    }

    GameObject FindPrefab(string name)
    {
        if (namedPrefabs == null) return null;
        foreach (var p in namedPrefabs)
            if (p != null && p.name == name) return p;
        return null;
    }

    void AddLabel(GameObject obj, string label, float confidence)
    {
        GameObject labelObj = new GameObject("Label_" + label);
        labelObj.transform.SetParent(obj.transform);
        labelObj.transform.localPosition = new Vector3(0, 2f, 0);
        TextMesh tm = labelObj.AddComponent<TextMesh>();
        tm.text = confidence > 0 ? label + "\n" + Mathf.Round(confidence * 100) + "%" : label;
        tm.fontSize = 24;
        tm.color = Color.white;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
    }
}

[System.Serializable]
public class SceneData
{
    public string case_id;
    public string case_title;
    public SceneObject[] objects;
}

[System.Serializable]
public class SceneObject
{
    public int id;
    public string label;
    public string prefab;
    public float confidence;
    public Vec3 position;
    public Vec3 rotation;
}

[System.Serializable]
public class Vec3
{
    public float x, y, z;
}
