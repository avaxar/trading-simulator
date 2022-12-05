import math
from typing import Callable, Tuple

import pygame

from . import utils


class Chart:
    FONT = utils.LARGE_FONT
    X_PRECISION_BASE = 15
    Y_PRECISION_BASE = 10

    def __init__(
        self,
        data_lambda: Callable[[float], float],
        width: int,
        height: int,
        *,
        x_margin=32,
        y_margin=64,
        scale_x_min=0.0,
        scale_x_max=100.0,
        scale_y_min=0.0,
        scale_y_max=100.0,
        x_repr=lambda x: str(x),
        y_repr=lambda y: str(y),
        fg_color=(255, 255, 255, 255),
        bg_color=(0, 0, 0, 0),
        nan_bg_color=(255, 0, 0, 128),
        gain_color=(0, 255, 0, 255),
        loss_color=(255, 0, 0, 255)
    ):
        self.data_lambda = data_lambda
        self.width = width
        self.height = height
        self.x_margin = x_margin
        self.y_margin = y_margin
        self.scale_x_min = scale_x_min
        self.scale_x_max = scale_x_max
        self.scale_y_min = scale_y_min
        self.scale_y_max = scale_y_max
        self.x_repr = x_repr
        self.y_repr = y_repr
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.nan_bg_color = nan_bg_color
        self.gain_color = gain_color
        self.loss_color = loss_color

        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)

    def at(self, x: float) -> Tuple[float, float]:
        if self.y_margin <= x <= self.width:
            ax = utils.lerp(
                x, self.y_margin, self.width, self.scale_x_min, self.scale_x_max
            )
            ay = self.data_lambda(ax)

            return ax, ay
        else:
            return math.nan, math.nan

    def adjust_scale(self, margin_perc=0.125):
        steps = [self.at(x)[1] for x in range(self.y_margin, self.width)]
        steps = [y for y in steps if not math.isnan(y) and not math.isinf(y)]

        if len(steps) == 0:
            return

        low = min(steps)
        high = max(steps)

        scale_y_min = low - (high - low) * margin_perc
        scale_y_max = high + (high - low) * margin_perc

        if scale_y_min != scale_y_max:
            self.scale_y_min = scale_y_min
            self.scale_y_max = scale_y_max

    def draw_overlay(self):
        x_precision = Chart.X_PRECISION_BASE ** math.floor(
            math.log(self.scale_x_max - self.scale_x_min, Chart.X_PRECISION_BASE)
        )
        y_precision = Chart.Y_PRECISION_BASE ** math.floor(
            math.log(self.scale_y_max - self.scale_y_min, Chart.Y_PRECISION_BASE)
        )

        ax = self.scale_x_min // x_precision * x_precision
        ay = self.scale_y_min // y_precision * y_precision

        pygame.draw.rect(
            self.surface,
            self.bg_color,
            ((0, self.height - self.x_margin), (self.width, self.x_margin)),
        )
        pygame.draw.line(
            self.surface,
            self.fg_color,
            (self.y_margin, self.height - self.x_margin),
            (self.width, self.height - self.x_margin),
            4,
        )

        while ax <= self.scale_x_max:
            x = utils.lerp(
                ax, self.scale_x_min, self.scale_x_max, self.y_margin, self.width
            )

            text = Chart.FONT.render(self.x_repr(ax), True, self.fg_color)
            text = pygame.transform.scale(
                text,
                (
                    int(text.get_width() * self.x_margin / text.get_height()),
                    self.x_margin,
                ),
            )
            self.surface.blit(
                text,
                (
                    x - text.get_width() / 2,
                    self.height - self.x_margin,
                ),
            )

            ax += x_precision

        pygame.draw.rect(
            self.surface, self.bg_color, ((0, 0), (self.y_margin, self.height))
        )
        pygame.draw.line(
            self.surface,
            self.fg_color,
            (self.y_margin, 0),
            (self.y_margin, self.height),
            4,
        )

        while ay <= self.scale_y_max:
            y = utils.lerp(
                ay, self.scale_y_min, self.scale_y_max, self.height - self.x_margin, 0
            )

            text = Chart.FONT.render(self.y_repr(ay), True, self.fg_color)
            text = pygame.transform.scale(
                text,
                (
                    self.y_margin,
                    int(text.get_height() * self.y_margin / text.get_width()),
                ),
            )
            self.surface.blit(text, (0, y - text.get_height() / 2))

            ay += y_precision

    def line_chart(self):
        if self.surface.get_size() != (self.width, self.height):
            self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        self.surface.fill(self.bg_color)

        prev_y = math.nan
        prev_stat = 0  # 1: gain; -1: loss
        for x in range(self.y_margin, self.width):
            ax, ay = self.at(x)

            if math.isnan(ay):
                prev_y = math.nan
                pygame.draw.line(
                    self.surface,
                    self.nan_bg_color,
                    (x, 0),
                    (x, self.height - self.x_margin),
                )
                continue

            y = utils.lerp(
                ay, self.scale_y_min, self.scale_y_max, self.height - self.x_margin, 0
            )

            if math.isnan(prev_y):
                prev_y = y
                continue

            # Remember that the Y axis is flipped
            if y < prev_y:
                pygame.draw.line(self.surface, self.gain_color, (x - 1, prev_y), (x, y))
                prev_stat = 1
            elif y > prev_y:
                pygame.draw.line(self.surface, self.loss_color, (x - 1, prev_y), (x, y))
                prev_stat = -1
            # These two can't be OR'd together above.
            elif prev_stat == 1:
                pygame.draw.line(self.surface, self.gain_color, (x - 1, prev_y), (x, y))
            elif prev_stat == -1:
                pygame.draw.line(self.surface, self.loss_color, (x - 1, prev_y), (x, y))
            else:
                pygame.draw.line(self.surface, self.fg_color, (x - 1, prev_y), (x, y))

            prev_y = y

        self.draw_overlay()

    # def candle_chart(self, candle_period=60):
    #     if self.surface.get_size() != (self.width, self.height):
    #         self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
    #
    #     self.surface.fill(self.bg_color)
    #
    #     for x in range(self.y_margin, self.width):
    #         ax, ay = self.at(x)
    #
    #     self.draw_overlay()
