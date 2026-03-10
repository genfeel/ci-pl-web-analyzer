import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { getCategoryColor } from './colors.js'

export class ContainerScene {
  constructor(canvas) {
    this.canvas = canvas
    this.scene = new THREE.Scene()
    this.scene.background = new THREE.Color(0xf0f2f5)
    this.boxMeshes = []
    this.raycaster = new THREE.Raycaster()
    this.mouse = new THREE.Vector2()
    this.onCaseClick = null

    // 렌더러
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
    this.renderer.setPixelRatio(window.devicePixelRatio)
    this.renderer.shadowMap.enabled = true

    // 카메라
    this.camera = new THREE.PerspectiveCamera(45, 1, 10, 100000)
    this.camera.position.set(15000, 12000, 15000)

    // 컨트롤
    this.controls = new OrbitControls(this.camera, canvas)
    this.controls.enableDamping = true
    this.controls.dampingFactor = 0.1

    // 조명
    const ambient = new THREE.AmbientLight(0xffffff, 0.6)
    this.scene.add(ambient)
    const dir = new THREE.DirectionalLight(0xffffff, 0.8)
    dir.position.set(10000, 15000, 10000)
    dir.castShadow = true
    this.scene.add(dir)

    // 바닥 그리드
    const grid = new THREE.GridHelper(30000, 30, 0xcccccc, 0xe0e0e0)
    grid.position.y = -1
    this.scene.add(grid)

    // 클릭 이벤트
    canvas.addEventListener('click', (e) => this._onClick(e))

    this._animate()
  }

  resize(width, height) {
    this.camera.aspect = width / height
    this.camera.updateProjectionMatrix()
    this.renderer.setSize(width, height)
  }

  clear() {
    for (const mesh of this.boxMeshes) {
      this.scene.remove(mesh)
      mesh.geometry.dispose()
      mesh.material.dispose()
    }
    this.boxMeshes = []
    // 컨테이너 와이어프레임 제거
    const toRemove = this.scene.children.filter(
      c => c.userData?.isContainer || c.userData?.isFloor
    )
    for (const obj of toRemove) {
      this.scene.remove(obj)
      if (obj.geometry) obj.geometry.dispose()
      if (obj.material) obj.material.dispose()
    }
  }

  drawContainer(dims) {
    const [l, w, h] = dims

    // 와이어프레임
    const geo = new THREE.BoxGeometry(l, h, w)
    const edges = new THREE.EdgesGeometry(geo)
    const line = new THREE.LineSegments(
      edges,
      new THREE.LineBasicMaterial({ color: 0x333333, linewidth: 2 })
    )
    line.position.set(l / 2, h / 2, w / 2)
    line.userData.isContainer = true
    this.scene.add(line)

    // 반투명 바닥
    const floorGeo = new THREE.PlaneGeometry(l, w)
    const floorMat = new THREE.MeshBasicMaterial({
      color: 0xbbdefb,
      transparent: true,
      opacity: 0.3,
      side: THREE.DoubleSide,
    })
    const floor = new THREE.Mesh(floorGeo, floorMat)
    floor.rotation.x = -Math.PI / 2
    floor.position.set(l / 2, 0.5, w / 2)
    floor.userData.isFloor = true
    this.scene.add(floor)

    // 카메라 위치 조정
    const maxDim = Math.max(l, w, h)
    this.camera.position.set(l * 1.2, h * 1.5, w * 1.8)
    this.controls.target.set(l / 2, h / 3, w / 2)
    this.controls.update()
  }

  drawCases(placedCases) {
    for (const pc of placedCases) {
      const [pl, pw, ph] = pc.dimensions
      const [px, py, pz] = pc.position
      const color = getCategoryColor(pc.category)

      const geo = new THREE.BoxGeometry(pl, ph, pw)
      const mat = new THREE.MeshPhongMaterial({
        color: new THREE.Color(color),
        transparent: true,
        opacity: 0.85,
      })
      const mesh = new THREE.Mesh(geo, mat)
      mesh.position.set(px + pl / 2, pz + ph / 2, py + pw / 2)
      mesh.castShadow = true
      mesh.receiveShadow = true
      mesh.userData = { caseData: pc }
      this.scene.add(mesh)
      this.boxMeshes.push(mesh)

      // 에지 라인
      const edgeGeo = new THREE.EdgesGeometry(geo)
      const edgeMat = new THREE.LineBasicMaterial({ color: 0x333333 })
      const edgeLine = new THREE.LineSegments(edgeGeo, edgeMat)
      edgeLine.position.copy(mesh.position)
      edgeLine.userData = { caseData: pc }
      this.scene.add(edgeLine)
      this.boxMeshes.push(edgeLine)
    }
  }

  _onClick(event) {
    const rect = this.canvas.getBoundingClientRect()
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

    this.raycaster.setFromCamera(this.mouse, this.camera)
    const meshes = this.boxMeshes.filter(m => m.isMesh)
    const intersects = this.raycaster.intersectObjects(meshes)

    if (intersects.length > 0 && this.onCaseClick) {
      const caseData = intersects[0].object.userData.caseData
      if (caseData) {
        this.onCaseClick(caseData, event.clientX, event.clientY)
      }
    } else if (this.onCaseClick) {
      this.onCaseClick(null)
    }
  }

  _animate() {
    requestAnimationFrame(() => this._animate())
    this.controls.update()
    this.renderer.render(this.scene, this.camera)
  }

  dispose() {
    this.clear()
    this.controls.dispose()
    this.renderer.dispose()
  }
}
