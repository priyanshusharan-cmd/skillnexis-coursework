using UnityEngine;
public class PlayerController : MonoBehaviour {
  public float speed = 5f; public int health = 3; public int score = 0;
  void Update() {
    float x=Input.GetAxisRaw("Horizontal"), y=Input.GetAxisRaw("Vertical");
    Vector2 direction=new Vector2(x,y).normalized;
    transform.position += (Vector3)(direction*speed*Time.deltaTime);
  }
  public void Collect(){score++;}
  public void TakeDamage(){health=Mathf.Max(0,health-1);}
}
