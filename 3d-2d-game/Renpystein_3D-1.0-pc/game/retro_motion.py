"""Responsive camera motion shared by the view, collision checks, and aim."""
import math


class Player:
    CAMERA_FOV = 90.0
    CAMERA_PLANE = math.tan(math.radians(CAMERA_FOV) / 2)
    LEGACY_CAMERA_PLANE = 0.66
    SPRINT_MULTIPLIER = 1.6
    # Short responses soften key presses; faster releases keep stopping precise.
    MOVE_RESPONSE = 0.055
    TURN_RESPONSE = 0.045
    MOVE_RELEASE = 0.030
    TURN_RELEASE = 0.020

    def __init__(self, wm, x, y, dirx, diry, planex, planey):
        self.wm = wm
        self.x, self.y = float(x), float(y)
        self.dirx, self.diry = float(dirx), float(diry)
        self.planex, self.planey = float(planex), float(planey)
        self.rot = math.atan2(diry, dirx)
        self.planerot = math.atan2(planey, planex)
        self.plane_offset = self.planerot - self.rot
        self.plane_length = self.CAMERA_PLANE
        self.planex = math.cos(self.planerot) * self.plane_length
        self.planey = math.sin(self.planerot) * self.plane_length
        self.moveSpeed = 4.5
        self.rotSpeed = math.pi / 2
        self.stop()
        self.floor_z = self.wm.session.heights.floor_at(self.x,self.y) if hasattr(self.wm.session,"heights") else 0.
        self.view_z = self.floor_z + .5

    @property
    def projection_scale(self):
        """Keep world height, width and perspective planes on the same lens."""
        return self.LEGACY_CAMERA_PLANE / self.plane_length

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.plane_length = self.CAMERA_PLANE
        self.planex = math.cos(self.planerot) * self.plane_length
        self.planey = math.sin(self.planerot) * self.plane_length
        self.stop()

        # The arena is a cyclic reference and may still be restoring its own
        # dictionary. Read only this player's saved values until rendering.
        self.floor_z=state.get('floor_z',0.)
        self.view_z=state.get('view_z',self.floor_z+.5)

    def stop(self):
        """Discard motion immediately on pause, focus loss, death, or exit."""
        self.speed = self.strafe = self.dir = 0
        self.sprinting = False
        self._forward_velocity = self._strafe_velocity = self._turn_velocity = 0.0

    @staticmethod
    def _ease(velocity, target, dt, response, release):
        response = release if target == 0 else response
        fraction = -math.expm1(-dt / response)
        # Integrate the eased velocity over this frame, rather than using its
        # endpoint. Travel and turn speed therefore stay consistent across FPS.
        distance = target * dt + (velocity - target) * response * fraction
        velocity += (target - velocity) * fraction
        return velocity, distance

    def move(self, dt):
        remaining = max(0.0, min(0.12, dt))
        while remaining > 1e-10:
            step = min(1.0 / 120, remaining)
            lift=self.wm.session.heights.lift_at(self.x,self.y) if hasattr(self.wm.session,'heights') else None
            riding=bool(lift and lift.moving)
            if riding:self._forward_velocity=self._strafe_velocity=0.
            pace = self.SPRINT_MULTIPLIER if self.sprinting else 1.0
            self._forward_velocity, forward = self._ease(
                self._forward_velocity, 0 if riding else self.speed * pace, step,
                self.MOVE_RESPONSE, self.MOVE_RELEASE)
            self._strafe_velocity, strafe = self._ease(
                self._strafe_velocity, 0 if riding else self.strafe * pace, step,
                self.MOVE_RESPONSE, self.MOVE_RELEASE)
            self._turn_velocity, turn = self._ease(
                self._turn_velocity, self.dir, step,
                self.TURN_RESPONSE, self.TURN_RELEASE)
            turn *= self.rotSpeed
            facing = self.rot + turn / 2
            forward *= self.moveSpeed
            strafe *= self.moveSpeed
            new_x = self.x + math.cos(facing) * forward - math.sin(facing) * strafe
            new_y = self.y + math.sin(facing) * forward + math.cos(facing) * strafe
            if not self.isBlocking(new_x, new_y):
                self.x, self.y = new_x, new_y
            elif not self.isBlocking(new_x, self.y):
                self.x = new_x
            elif not self.isBlocking(self.x, new_y):
                self.y = new_y
            self.rot = (self.rot + turn) % math.tau
            if hasattr(self.wm.session,"heights"):
                self.floor_z = self.wm.session.heights.floor_at(self.x,self.y)
                self.view_z += (self.floor_z+.5-self.view_z)*(-math.expm1(-step/.055))
            remaining -= step

        if hasattr(self.wm.session,"heights"):
            self.floor_z=self.wm.session.heights.floor_at(self.x,self.y)
            if not hasattr(self,"view_z"):self.view_z=self.floor_z+.5

        self.planerot = (self.rot + self.plane_offset) % math.tau
        self.dirx, self.diry = math.cos(self.rot), math.sin(self.rot)
        self.planex = math.cos(self.planerot) * self.plane_length
        self.planey = math.sin(self.planerot) * self.plane_length

    def isBlocking(self, x, y):
        if hasattr(self.wm.session,"heights"):
            source=self.wm.session.heights.floor_at(self.x,self.y)
            return not self.wm.session.can_occupy(x,y,from_floor=source,from_pos=(self.x,self.y),allow_drop=True)
        return not self.wm.session.can_occupy(x, y)
