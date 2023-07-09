from ctypes.wintypes import HGLOBAL
import sys, os, random, pygame

WIDTH, HEIGHT = 1280, 960

class Block(pygame.sprite.Sprite):
	def __init__(self, path, x_pos, y_pos):
		super().__init__()

		self.image = pygame.transform.rotate(pygame.image.load(path), 90)
		self.rect = self.image.get_rect(center = (x_pos, y_pos))

class Paddle(Block):
	def __init__(self, path, x_pos, y_pos, speed):
		super().__init__(path, x_pos, y_pos)
		
		self.speed = speed
		self.movement = 0

	def on_screen(self):
		if self.rect.left < 0:
			self.rect.left = 0
		if self.rect.right > WIDTH:
			self.rect.right = WIDTH

	def update(self, ball_group):
		self.rect.x += self.movement
		self.on_screen()
	
	def reset_paddle(self):
		self.rect.center = (WIDTH/2, HEIGHT - 60)

class Ball(Block):
	def __init__(self, path, x_pos, y_pos, x_speed, y_speed, paddles):
		super().__init__(path, x_pos, y_pos)
		
		self.x_speed = x_speed * random.choice((1, -1))
		self.y_speed = y_speed
		self.paddles = paddles
		self.active = False
		self.score_time = 0

	def update(self):
		if self.active:
			self.rect.y += self.y_speed
			self.rect.x += self.x_speed
			self.collisions()
		else:
			self.restart_counter()
	
	def collisions(self):
		if self.rect.left <= 0 or self.rect.right >= WIDTH:
			pygame.mixer.Sound.play(bounce_sound)
			self.x_speed *= -1
		if self.rect.top <= 0:
			self.y_speed *= -1
		
		if pygame.sprite.spritecollide(self, self.paddles, False):
			pygame.mixer.Sound.play(bounce_sound)
			collision_paddle = pygame.sprite.spritecollide(self, self.paddles, False)[0].rect
			if abs(self.rect.right - collision_paddle.left) < 10 and self.x_speed > 0:
				self.x_speed *= -1
			if abs(self.rect.left - collision_paddle.right) < 10 and self.x_speed < 0:
				self.x_speed *= -1
			if abs(self.rect.top - collision_paddle.bottom) < 10 and self.y_speed < 0:
				self.rect.top = collision_paddle.bottom
				self.y_speed *= -1
			if abs(self.rect.bottom - collision_paddle.top) < 10 and self.y_speed > 0:
				self.rect.bottom = collision_paddle.top
				self.y_speed *= -1

	def reset_ball(self):
		self.active = False
		self.x_speed *= random.choice((1, -1))
		self.y_speed = -4
		self.rect.center = (WIDTH/2, 3*HEIGHT/4)
		self.score_time = pygame.time.get_ticks()
	
	def restart_counter(self):
		current_time = pygame.time.get_ticks()
		countdown_time = 3

		if current_time - self.score_time <= 700:
			countdown_time = 3
		if 700 < current_time - self.score_time <= 1400:
			countdown_time = 2
		if 1400 < current_time - self.score_time <= 2100:
			countdown_time = 1
		if current_time - self.score_time >= 2100:
			self.active = True

		time_counter = game_font.render(str(countdown_time), True, accent_color)
		time_counter_pos = time_counter.get_rect(center = (WIDTH/2, HEIGHT/2 + 50))
		pygame.draw.rect(screen, bg_color, time_counter_pos)
		screen.blit(time_counter,time_counter_pos)

class Brick(pygame.sprite.Sprite):
	def __init__(self, x_pos, y_pos, width, height, health, colors):
		self.x = x_pos
		self.y = y_pos
		self.width = width
		self.height = height

		self.health = health
		self.max_health = health

		self.colors = colors
		self.color = colors[0]


	def draw(self):
		pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

	def collide(self, ball):
		if not (ball.rect.x <= self.x + self.width and ball.rect.x >= self.x):
			return False
		if not (ball.rect.y - (ball.rect.bottom - ball.rect.top)/2 <= self.y + self.height):
			return False
		self.hit()
		if self.health == 0:
			pygame.mixer.Sound.play(score_sound)
		else:
			pygame.mixer.Sound.play(bounce_sound)
		self.update()
		pygame.display.flip()
		pygame.display.update()
		game_manager.player_score += 1
		return True

	def hit(self):
		self.health -= 1
		ball.y_speed *= -1
		self.color = self.interpolate(*self.colors, self.health/self.max_health)
		pygame.display.flip()
		pygame.display.update()

	@staticmethod
	def interpolate(color_a, color_b, t):
		# 'color_a' and 'color_b' are RGB tuples
		# 't' is a value between 0.0 and 1.0
		# this is a naive interpolation
		return tuple(int(b + (a - b) * t) for a, b in zip(color_a, color_b))

	def generate_bricks(rows, cols):
		gap = 5
		brick_width = WIDTH // cols - gap
		brick_height = 50

		bricks = []

		for row in range(rows):
			for col in range(cols):
				brick = Brick(2 + col * brick_width + gap * col, 100 + row * brick_height +
							gap * row, brick_width, brick_height, game_manager.row_health[row], [hover_color, (160, 160, 160)])
				bricks.append(brick)
		return bricks

	def update(self):
		self.draw()

class GameManager:
	def __init__(self,ball_group,paddle_group):
		self.player_score = 0
		self.ball_group = ball_group
		self.paddle_group = paddle_group

		self.easy = 1
		self.normal = 2
		self.hard = 3
		self.mode = self.normal

		self.start_lives = 3
		self.lives = self.start_lives
		self.row_health = [3, 2 , 1]

		self.row = 3
		self.col = 6

	def run_game(self):
		# Drawing the game objects
		self.paddle_group.draw(screen)
		self.ball_group.draw(screen)
		self.draw()

		# Updating the game objects
		self.paddle_group.update(self.ball_group)
		self.ball_group.update()
		self.draw()

	def set_difficulty(self, mode):
		if mode == easy:
			self.row = 2
			self.col = 3
			self.start_lives = 5
			self.row_health = [2 , 1]
			print("Easy mode")
		if mode == normal:
			self.row = 3
			self.col = 6
			self.start_lives = 3
			self.row_health = [3, 2 , 1]
			print("Normal Mode")
		if mode == hard:
			self.row = 5
			self.col = 10
			self.start_lives = 1
			self.row_health = [5, 4, 3, 2 , 1]
			print("Hard Mode")
		self.lives = self.start_lives
		self.mode = mode

	def reset_game(self):
		self.ball_group.sprite.reset_ball()
		self.player_score = 0
		self.paddle_group.sprite.reset_paddle()
		self.set_difficulty(self.mode)

	def draw(self):
		playerScore = game_font.render(str(self.player_score), True, accent_color)
		player_score_rect = playerScore.get_rect(center = (WIDTH/2, HEIGHT/2 + 100))
		screen.blit(playerScore, player_score_rect)

		lives_text = game_font.render(f"Lives: {self.lives}", 1, accent_color)
		screen.blit(lives_text, (WIDTH - 135, HEIGHT - lives_text.get_height() - 10))
		pygame.display.update()
	
	def display_text(self, text):
		text_render = menu_font.render(text, 1, hover_color)
		screen.blit(text_render, (WIDTH/2 - text_render.get_width() / 2, HEIGHT/2 - text_render.get_height()/2))
		pygame.display.update()
		pygame.time.delay(3000)

class Button():
	def __init__(self, image, pos, text_input, font, base_color, hovering_color):
		self.x_pos = pos[0]
		self.y_pos = pos[1]

		self.font = font
		self.base_color, self.hovering_color = base_color, hovering_color
		self.text_input = text_input
		self.text = self.font.render(self.text_input, True, self.base_color)
		
		self.image = image
		if self.image is None:
			self.image = self.text
		self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
		self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

	def update(self, screen):
		if self.image is not None:
			screen.blit(self.image, self.rect)
		screen.blit(self.text, self.text_rect)

	def checkForInput(self, position):
		if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
			pygame.mixer.Sound.play(bounce_sound)
			return True
		return False

	def changeColor(self, position):
		if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
			self.text = self.font.render(self.text_input, True, self.hovering_color)
		else:
			self.text = self.font.render(self.text_input, True, self.base_color)

# General setup
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
clock = pygame.time.Clock()

# Main Window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Brick Braker')

# Global Variables
bg_color = pygame.Color(100, 50, 200)
accent_color = (200, 200, 200)
hover_color = (255, 255, 255)
menu_font = pygame.font.Font('freesansbold.ttf', 128)
submenu_font = pygame.font.Font('freesansbold.ttf',64)
game_font = pygame.font.Font('freesansbold.ttf', 32)

bounce_sound = pygame.mixer.Sound("bounce.ogg")
bounce_sound.set_volume(0.25)
score_sound = pygame.mixer.Sound("score.ogg")
score_sound.set_volume(0.25)

# Game objects
player = Paddle('Paddle.png', WIDTH/2, HEIGHT - 60, 6)
paddle_group = pygame.sprite.GroupSingle()
paddle_group.add(player)

ball = Ball('Ball.png', WIDTH/2, 3*HEIGHT/4, 4, -4, paddle_group)
ball_sprite = pygame.sprite.GroupSingle()
ball_sprite.add(ball)

game_manager = GameManager(ball_sprite,paddle_group)

easy = game_manager.easy
normal = game_manager.normal
hard = game_manager.hard

def play():

	bricks = Brick.generate_bricks(game_manager.row, game_manager.col)

	while True:
		# Background Stuff
		screen.fill(bg_color)
		mouse_pos = pygame.mouse.get_pos()

		back_button = Button(image = None, pos = (50, HEIGHT - 25 ), text_input = "Back", font = game_font, base_color = accent_color, hovering_color = hover_color)
		back_button.changeColor(mouse_pos)
		back_button.update(screen)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.MOUSEBUTTONDOWN:
				if back_button.checkForInput(mouse_pos):
					game_manager.reset_game()
					main()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					game_manager.reset_game()
					main()
				if event.key == pygame.K_LEFT:
					player.movement -= player.speed
				if event.key == pygame.K_RIGHT:
					player.movement += player.speed
			if event.type == pygame.KEYUP:
				if event.key == pygame.K_LEFT:
					player.movement += player.speed
				if event.key == pygame.K_RIGHT:
					player.movement -= player.speed

		for brick in bricks[:]:
			brick.collide(ball)

			if brick.health <= 0:
				bricks.remove(brick)
			brick.update()

		# lives check
		if ball.rect.bottom >= HEIGHT:
			game_manager.lives -= 1
			ball.reset_ball()
			player.reset_paddle()

		if game_manager.lives <= 0:
			game_manager.display_text("You Lost!")
			game_manager.lives = game_manager.start_lives
			game_manager.reset_game()
			bricks = Brick.generate_bricks(game_manager.row, game_manager.col)

		if len(bricks) == 0:
			game_manager.display_text("You Won!")
			game_manager.lives = game_manager.start_lives
			game_manager.reset_game()
			bricks = Brick.generate_bricks(game_manager.row, game_manager.col)

		# Run the game
		game_manager.run_game()

		# Rendering
		pygame.display.flip()
		pygame.display.update()
		clock.tick(120)

def options():
	while True:

		# Background Stuff
		screen.fill(bg_color)
		mouse_pos = pygame.mouse.get_pos()

		# Menu Window
		menu_text = submenu_font.render("Select difficulty :", True, hover_color)
		menu_rect = menu_text.get_rect(center = (WIDTH / 2, 250))
		screen.blit(menu_text, menu_rect)

		easy_button = Button(image = None, pos = (WIDTH/2, HEIGHT/2 - 80 ), text_input = "Easy", font = submenu_font, base_color = accent_color, hovering_color = hover_color)
		normal_button = Button(image = None, pos = (WIDTH/2, HEIGHT/2 + 20 ), text_input = "Normal", font = submenu_font, base_color = accent_color, hovering_color = hover_color)
		hard_button = Button(image = None, pos = (WIDTH/2, HEIGHT/2 + 120 ), text_input = "Hard", font = submenu_font, base_color = accent_color, hovering_color = hover_color)
		back_button = Button(image = None, pos = (WIDTH/2, HEIGHT/2 + 320 ), text_input = "Back", font = submenu_font, base_color = accent_color, hovering_color = hover_color)
		buttons = [easy_button, normal_button, hard_button, back_button]

		for button in buttons:
			button.changeColor(mouse_pos)
			button.update(screen)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					main()
			if event.type == pygame.MOUSEBUTTONDOWN:
				if back_button.checkForInput(mouse_pos):
					main()
				if easy_button.checkForInput(mouse_pos):
					game_manager.set_difficulty(easy)
				if normal_button.checkForInput(mouse_pos):
					game_manager.set_difficulty(normal)
				if hard_button.checkForInput(mouse_pos):
					game_manager.set_difficulty(hard)

		pygame.display.flip()
		pygame.display.update()

def main():
	while True:
		# Background Stuff
		screen.fill(bg_color)
		mouse_pos = pygame.mouse.get_pos()

		# Menu Window
		menu_text = menu_font.render("Brick Breaker", True, hover_color)
		menu_rect = menu_text.get_rect(center = (WIDTH / 2, 200))
		screen.blit(menu_text, menu_rect)

		play_button = Button(image = None, pos = (WIDTH/2, HEIGHT/2 - 20 ), text_input ="Play", font = submenu_font, base_color = (200, 200, 200), hovering_color = (255, 255, 255))
		options_button = Button(image = None, pos = (WIDTH/2, HEIGHT/2 + 80), text_input ="Options", font = submenu_font, base_color = (200, 200, 200), hovering_color = (255, 255, 255))
		quit_button = Button(image = None, pos = (WIDTH/2, HEIGHT/2 + 180), text_input ="Quit", font = submenu_font, base_color = (200, 200, 200), hovering_color = (255, 255, 255))
		buttons = [play_button, options_button, quit_button]

		for button in buttons:
			button.changeColor(mouse_pos)
			button.update(screen)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					pygame.quit()
					sys.exit()
			if event.type == pygame.MOUSEBUTTONDOWN:
				if play_button.checkForInput(mouse_pos):
					play()
				if options_button.checkForInput(mouse_pos):
					options()
				if quit_button.checkForInput(mouse_pos):
					pygame.quit()
					sys.exit()

		pygame.display.flip()
		pygame.display.update()

if __name__ == "__main__":
	local_dir = os.path.dirname(__file__)
	main()