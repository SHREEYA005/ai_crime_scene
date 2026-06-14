using UnityEngine;
using System.Collections;
using UnityEngine.Networking;

public class SceneLoader : MonoBehaviour
{
    void Start()
    {
        StartCoroutine(LoadScene());
    }

    IEnumerator LoadScene()
    {
        string url = Application.absoluteURL;
        string caseId = "1";

        if (url.Contains("case_id="))
        {
            int idx = url.IndexOf("case_id=") + 8;
            int end = url.IndexOf("&", idx);
            caseId = end > 0 ? url.Substring(idx, end - idx) : url.Substring(idx);
        }

        string jsonUrl = "/cases/" + caseId + "/scene-data";
        Debug.Log("Fetching scene from: " + jsonUrl);

        UnityWebRequest req = UnityWebRequest.Get(jsonUrl);
        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("Failed to load scene: " + req.error);
            yield break;
        }

        SceneData data = JsonUtility.FromJson<SceneData>(req.downloadHandler.text);
        if (data == null || data.objects == null)
        {
            Debug.LogError("Failed to parse JSON");
            yield break;
        }

        Debug.Log("Loaded: " + data.case_title + " with " + data.objects.Length + " objects");
        foreach (var obj in data.objects)
            SpawnObject(obj);
    }

    void SpawnObject(SceneObject obj)
    {
        Vector3 pos = new Vector3(obj.position.x, obj.position.y, obj.position.z);
        GameObject instance = GameObject.CreatePrimitive(PrimitiveType.Cube);
        instance.transform.position = pos;
        instance.transform.localScale = new Vector3(0.5f, 1.8f, 0.5f);
        instance.name = obj.label + "_" + obj.id;

        Material mat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
        if (obj.label == "person") mat.color = Color.red;
        else if (obj.label == "bloodstain") mat.color = new Color(0.6f, 0f, 0f);
        else if (obj.label == "body") mat.color = new Color(0.2f, 0.2f, 0.8f);
        else if (obj.label == "weapon" || obj.label == "knife" || obj.label == "handgun") mat.color = Color.yellow;
        else mat.color = Color.white;
        instance.GetComponent<Renderer>().material = mat;

        GameObject labelObj = new GameObject("Label");
        labelObj.transform.SetParent(instance.transform);
        labelObj.transform.localPosition = new Vector3(0, 2f, 0);
        TextMesh tm = labelObj.AddComponent<TextMesh>();
        tm.text = obj.confidence > 0 ? obj.label + "\n" + Mathf.Round(obj.confidence * 100) + "%" : obj.label;
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
    public float confidence;
    public Vec3 position;
    public Vec3 rotation;
}

[System.Serializable]
public class Vec3
{
    public float x, y, z;
}