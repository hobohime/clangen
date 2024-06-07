from typing import Union, Tuple
import html

import pygame
import pygame_gui
from pygame_gui.core import UIContainer
from pygame_gui.core.gui_type_hints import RectLike, Coordinate
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.core.text.html_parser import HTMLParser
from pygame_gui.core.text.text_box_layout import TextBoxLayout
from pygame_gui.core.utility import translate
from pygame_gui.elements import UIAutoResizingContainer

from scripts.game_structure import image_cache

from scripts.utility import scale


class UIImageButton(pygame_gui.elements.UIButton):
    """Subclass of pygame_gui's button class. This allows for auto-scaling of the
    button image."""

    def _set_any_images_from_theme(self):
        changed = False
        normal_image = None
        try:
            normal_image = self.ui_theme.get_image(
                "normal_image", self.combined_element_ids
            )
            normal_image = pygame.transform.scale(
                normal_image, self.relative_rect.size
            )  # auto-rescale the image
        except LookupError:
            normal_image = None
        finally:
            if normal_image != self.normal_image:
                self.normal_image = normal_image
                self.hovered_image = normal_image
                self.selected_image = normal_image
                self.disabled_image = normal_image
                changed = True

        hovered_image = None
        try:
            hovered_image = self.ui_theme.get_image(
                "hovered_image", self.combined_element_ids
            )
            hovered_image = pygame.transform.scale(
                hovered_image, self.relative_rect.size
            )  # auto-rescale the image
        except LookupError:
            hovered_image = self.normal_image
        finally:
            if hovered_image != self.hovered_image:
                self.hovered_image = hovered_image
                changed = True

        selected_image = None
        try:
            selected_image = self.ui_theme.get_image(
                "selected_image", self.combined_element_ids
            )
            selected_image = pygame.transform.scale(
                selected_image, self.relative_rect.size
            )  # auto-rescale the image
        except LookupError:
            selected_image = self.normal_image
        finally:
            if selected_image != self.selected_image:
                self.selected_image = selected_image
                changed = True

        disabled_image = None
        try:
            disabled_image = self.ui_theme.get_image(
                "disabled_image", self.combined_element_ids
            )
            disabled_image = pygame.transform.scale(
                disabled_image, self.relative_rect.size
            )  # auto-rescale the image
        except LookupError:
            disabled_image = self.normal_image
        finally:
            if disabled_image != self.disabled_image:
                self.disabled_image = disabled_image
                changed = True

        return changed


class UIModifiedScrollingContainer(pygame_gui.elements.UIScrollingContainer):
    def __init__(self, relative_rect: pygame.Rect, manager=None, starting_height: int = 1,
                 container=None, parent_element=None, object_id=None, anchors=None, visible: int = 1):
        super().__init__(relative_rect=relative_rect, manager=manager, starting_height=starting_height,
                         container=container, parent_element=parent_element, object_id=object_id, anchors=anchors,
                         visible=visible)

    def _sort_out_element_container_scroll_bars(self):
        """
        This creates, re-sizes or removes the scrollbars after resizing, but not after the scroll
        bar has been moved. Instead it tries to keep the scrollbars in the same approximate position
        they were in before resizing
        """
        self._check_scroll_bars_and_adjust()
        need_horiz_scroll_bar, need_vert_scroll_bar = self._check_scroll_bars_and_adjust()
        print(f"scroll{need_vert_scroll_bar}")
        self.scroll_bar_width = 30
        if need_vert_scroll_bar:
            vis_percent = self._view_container.rect.height / self.scrolling_height
            if self.vert_scroll_bar is None:
                print(self.scroll_bar_width)
                scroll_bar_rect = pygame.Rect(-self.scroll_bar_width,
                                              0,
                                              self.scroll_bar_width,
                                              self._view_container.rect.height)
                self.vert_scroll_bar = UIImageVerticalScrollBar(relative_rect=scroll_bar_rect,
                                                                visible_percentage=vis_percent,
                                                                manager=self.ui_manager,
                                                                container=self._root_container,
                                                                parent_element=self,
                                                                anchors={'left': 'right',
                                                                         'right': 'right',
                                                                         'top': 'top',
                                                                         'bottom': 'bottom'})
                print(self.vert_scroll_bar)
                self.join_focus_sets(self.vert_scroll_bar)
            else:
                start_percent = ((self._view_container.rect.top -
                                  self.scrollable_container.rect.top)
                                 / self.scrolling_height)
                self.vert_scroll_bar.start_percentage = start_percent
                self.vert_scroll_bar.set_visible_percentage(vis_percent)
                self.vert_scroll_bar.set_dimensions((self.scroll_bar_width,
                                                     self._view_container.rect.height))
        else:
            self._remove_vert_scrollbar()

        if need_horiz_scroll_bar:
            vis_percent = self._view_container.rect.width / self.scrolling_width
            if self.horiz_scroll_bar is None:
                self.scroll_bar_height = 20
                scroll_bar_rect = pygame.Rect(0,
                                              -self.scroll_bar_height,
                                              self._view_container.rect.width,
                                              self.scroll_bar_height)
                self.horiz_scroll_bar = pygame_gui.elements.UIHorizontalScrollBar(relative_rect=scroll_bar_rect,
                                                                                  visible_percentage=vis_percent,
                                                                                  manager=self.ui_manager,
                                                                                  container=self._root_container,
                                                                                  parent_element=self,
                                                                                  anchors={'left': 'left',
                                                                                           'right': 'right',
                                                                                           'top': 'bottom',
                                                                                           'bottom': 'bottom'})
                self.join_focus_sets(self.horiz_scroll_bar)
            else:
                start_percent = ((self._view_container.rect.left -
                                  self.scrollable_container.rect.left)
                                 / self.scrolling_width)
                self.horiz_scroll_bar.start_percentage = start_percent
                self.horiz_scroll_bar.set_visible_percentage(vis_percent)
                self.horiz_scroll_bar.set_dimensions((self._view_container.rect.width,
                                                      self.scroll_bar_height))
        else:
            self._remove_horiz_scrollbar()

    def set_scrollable_area_dimensions(self, dimensions: Union[pygame.math.Vector2,
                                                               Tuple[int, int],
                                                               Tuple[float, float]]):
        """
        Set the size of the scrollable area container. It starts the same size as the view
        container but often you want to expand it, or why have a scrollable container?

        :param dimensions: The new dimensions.
        """
        self.scrollable_container.set_dimensions(dimensions)

        self._calculate_scrolling_dimensions()
        self._sort_out_element_container_scroll_bars()


class UIImageVerticalScrollBar(pygame_gui.elements.UIVerticalScrollBar):
    def __init__(self, relative_rect: pygame.Rect, visible_percentage: float, manager=None, container=None,
                 parent_element=None, object_id=None, anchors=None, visible: int = 1):
        super().__init__(relative_rect=relative_rect, visible_percentage=visible_percentage, manager=manager,
                         container=container, parent_element=parent_element, object_id=object_id, anchors=anchors,
                         visible=visible)
        self.top_button.kill()
        self.top_button = UIImageButton(scale(pygame.Rect((0, 0),
                                                          (44, 40))),
                                        text='',
                                        manager=self.ui_manager,
                                        container=self.button_container,
                                        starting_height=1,
                                        parent_element=self,
                                        object_id="#vertical_slider_up_arrow_button",
                                        anchors={'left': 'left',
                                                 'right': 'right',
                                                 'top': 'top',
                                                 'bottom': 'top'}
                                        )

        self.bottom_button.kill()
        self.bottom_button = UIImageButton(scale(pygame.Rect((0, -self.arrow_button_height),
                                                             (44, 40))),
                                           text='',
                                           manager=self.ui_manager,
                                           container=self.button_container,
                                           starting_height=1,
                                           parent_element=self,
                                           object_id="#vertical_slider_down_arrow_button",
                                           anchors={'left': 'left',
                                                    'right': 'right',
                                                    'top': 'bottom',
                                                    'bottom': 'bottom'}
                                           )


class UIImageHorizontalSlider(pygame_gui.elements.UIHorizontalSlider):
    """
    a subclass of UIHorizontalSlider, this is really only meant for one size and appearance of slider, though could
    be modified to allow for more customizability.  As we currently only use horizontal sliders in one spot and I
    don't forsee future additional sliders, I will leave it as is for now.
    """

    def __init__(self, relative_rect, start_value,
                 value_range, click_increment=None, object_id=None,
                 manager=None):
        super().__init__(relative_rect=relative_rect, start_value=start_value, value_range=value_range,
                         click_increment=click_increment, object_id=object_id, manager=manager)

        # kill the sliding button that the UIHorizontalSlider class makes, then make it again
        self.sliding_button.kill()
        sliding_x_pos = int(self.background_rect.width / 2 - self.sliding_button_width / 2)
        self.sliding_button = UIImageButton(scale(pygame.Rect((sliding_x_pos, 0),
                                                              (60,
                                                               44))),
                                            text='',
                                            manager=self.ui_manager,
                                            container=self.button_container,
                                            starting_height=1,
                                            parent_element=self,
                                            object_id="#horizontal_slider_button",
                                            anchors={'left': 'left',
                                                     'right': 'left',
                                                     'top': 'top',
                                                     'bottom': 'bottom'},
                                            visible=self.visible
                                            )

        # reset start value, for some reason it defaults to 50 otherwise
        self.set_current_value(start_value)
        # set hold range manually since using UIImageButton breaks it?
        self.sliding_button.set_hold_range((1600, 1400))

        # kill and remake the left button
        self.left_button.kill()
        self.left_button = UIImageButton(scale(pygame.Rect((0, 0),
                                                           (40, 44))),
                                         text='',
                                         manager=self.ui_manager,
                                         container=self.button_container,
                                         starting_height=1,
                                         parent_element=self,
                                         object_id="#horizontal_slider_left_arrow_button",
                                         anchors={'left': 'left',
                                                  'right': 'left',
                                                  'top': 'top',
                                                  'bottom': 'bottom'},
                                         visible=self.visible
                                         )

        # kill and remake the right button
        self.right_button.kill()
        self.right_button = UIImageButton(scale(pygame.Rect((-self.arrow_button_width, 0),
                                                            (40, 44))),
                                          text='',
                                          manager=self.ui_manager,
                                          container=self.button_container,
                                          starting_height=1,
                                          parent_element=self,
                                          object_id="#horizontal_slider_right_arrow_button",
                                          anchors={'left': 'right',
                                                   'right': 'right',
                                                   'top': 'top',
                                                   'bottom': 'bottom'},
                                          visible=self.visible
                                          )


class UISpriteButton():
    """This is for use with the cat sprites. It wraps together a UIImage and Transparent Button.
    For most functions, this can be used exactly like other pygame_gui elements."""

    def __init__(
            self,
            relative_rect,
            sprite,
            cat_id=None,
            visible=1,
            cat_object=None,
            starting_height=1,
            manager=None,
            container=None,
            object_id=None,
            tool_tip_text=None,
    ):

        # We have to scale the image before putting it into the image object. Otherwise, the method of upscaling that
        # UIImage uses will make the pixel art fuzzy
        self.image = pygame_gui.elements.UIImage(
            relative_rect,
            pygame.transform.scale(sprite, relative_rect.size),
            visible=visible,
            manager=manager,
            container=container,
            object_id=object_id,
        )
        self.image.disable()
        # The transparent button. This a subclass that UIButton that also hold the cat_id.

        self.button = CatButton(
            relative_rect,
            "",
            object_id="#cat_button",
            visible=visible,
            cat_id=cat_id,
            cat_object=cat_object,
            starting_height=starting_height,
            manager=manager,
            tool_tip_text=tool_tip_text,
            container=container,
        )

    def return_cat_id(self):
        return self.button.return_cat_id()

    def return_cat_object(self):
        return self.button.return_cat_object()

    def enable(self):
        self.button.enable()

    def disable(self):
        self.button.disable()

    def hide(self):
        self.image.hide()
        self.button.hide()

    def show(self):
        self.image.show()
        self.button.show()

    def kill(self):
        self.button.kill()
        self.image.kill()
        del self

    def set_image(self, new_image):
        self.image.set_image(new_image)

    """This is to simplify event handling. Rather that writing 
            'if event.ui_element = cat_sprite_object.button'
            you can treat is as any other single pygame UI element and write:
            'if event.ui_element = cat_sprite_object. """

    def __eq__(self, __o: object) -> bool:
        if self.button == __o:
            return True
        else:
            return False


class CatButton(UIImageButton):
    """Basic UIButton subclass for at sprite buttons. It stores the cat ID.
    Can also be used as a general button that holds some data"""

    def __init__(
            self,
            relative_rect,
            text,
            cat_id=None,
            visible=True,
            cat_object=None,
            starting_height=1,
            parent_element=None,
            object_id=None,
            manager=None,
            tool_tip_text=None,
            container=None,
    ):
        self.cat_id = cat_id
        self.cat_object = cat_object
        super().__init__(
            relative_rect,
            text,
            object_id=object_id,
            visible=visible,
            parent_element=parent_element,
            starting_height=starting_height,
            manager=manager,
            tool_tip_text=tool_tip_text,
            container=container,
        )

    def return_cat_id(self):
        return self.cat_id

    def return_cat_object(self):
        return self.cat_object

    def set_id(self, id):
        self.cat_id = id


class UITextBoxTweaked(pygame_gui.elements.UITextBox):
    """The default class has 1.25 line spacing. It would be fairly easy to allow the user to change that,
    but it doesn't allow it... for some reason This class only exists as a way to specify the line spacing. Please
    only use if you want to have control over the line spacing."""

    def __init__(
            self,
            html_text: str,
            relative_rect,
            manager=None,
            line_spacing=1,
            wrap_to_height: bool = False,
            starting_height: int = 1,
            container=None,
            parent_element=None,
            object_id=None,
            anchors=None,
            visible: int = 1,
            *,
            pre_parsing_enabled: bool = True,
            text_kwargs=None,
            allow_split_dashes: bool = True
    ):

        self.line_spaceing = line_spacing

        super().__init__(
            html_text,
            relative_rect,
            manager=manager,
            container=container,
            starting_height=starting_height,
            wrap_to_height=wrap_to_height,
            parent_element=parent_element,
            anchors=anchors,
            object_id=object_id,
            visible=visible,
            pre_parsing_enabled=pre_parsing_enabled,
            text_kwargs=text_kwargs,
            allow_split_dashes=allow_split_dashes,
        )

    # 99% of this is copy-pasted from the original function.
    def _reparse_and_rebuild(self):
        self.parser = HTMLParser(
            self.ui_theme,
            self.combined_element_ids,
            self.link_style,
            line_spacing=self.line_spaceing,
        )  # THIS IS THE ONLY LINE CHANGED WITH THIS SUBCLASS
        self.rebuild()

    # 99% of this is copy-pasted from the original function.
    def parse_html_into_style_data(self):
        """
        Parses HTML styled string text into a format more useful for styling pygame.freetype
        rendered text.
        """
        feed_input = self.html_text
        if self.plain_text_display_only:
            feed_input = html.escape(
                feed_input
            )  # might have to add true to second param here for quotes
        feed_input = self._pre_parse_text(
            translate(feed_input, **self.text_kwargs) + self.appended_text
        )
        self.parser.feed(feed_input)

        default_font = self.ui_theme.get_font_dictionary().find_font(
            font_name=self.parser.default_style["font_name"],
            font_size=self.parser.default_style["font_size"],
            bold=self.parser.default_style["bold"],
            italic=self.parser.default_style["italic"],
        )
        default_font_data = {
            "font": default_font,
            "font_colour": self.parser.default_style["font_colour"],
            "bg_colour": self.parser.default_style["bg_colour"],
        }
        self.text_box_layout = TextBoxLayout(
            self.parser.layout_rect_queue,
            pygame.Rect((0, 0), (self.text_wrap_rect[2], self.text_wrap_rect[3])),
            pygame.Rect((0, 0), (self.text_wrap_rect[2], self.text_wrap_rect[3])),
            line_spacing=self.line_spaceing,
            # THIS IS THE ONLY LINE CHANGED WITH THIS SUBCLASS
            default_font_data=default_font_data,
            allow_split_dashes=self.allow_split_dashes,
        )
        self.parser.empty_layout_queue()
        if self.text_wrap_rect[3] == -1:
            self.text_box_layout.view_rect.height = (
                self.text_box_layout.layout_rect.height
            )

        self._align_all_text_rows()
        self.text_box_layout.finalise_to_new()


class UIRelationStatusBar:
    """Wraps together a status bar"""

    def __init__(
            self,
            relative_rect,
            percent_full=0,
            positive_trait=True,
            dark_mode=False,
            manager=None,
            style="bars",
    ):

        # Change the color of the bar depending on the value and if it's a negative or positive trait
        if percent_full > 49:
            if positive_trait:
                theme = "#relation_bar_pos"
            else:
                theme = "#relation_bar_neg"
        else:
            theme = "#relation_bar"

        # Determine dark mode or light mode
        if dark_mode:
            theme += "_dark"

        self.status_bar = pygame_gui.elements.UIStatusBar(
            relative_rect, object_id=theme, manager=manager
        )
        self.status_bar.percent_full = percent_full / 100

        # Now to make the overlay
        overlay_path = "resources/images/"
        if style == "bars":
            if dark_mode:
                overlay_path += "relations_border_bars_dark.png"
            else:
                overlay_path += "relations_border_bars.png"
        elif style == "dots":
            if dark_mode:
                overlay_path += "relations_border_dots_dark.png"
            else:
                overlay_path += "relations_border_dots.png"

        image = pygame.transform.scale(
            image_cache.load_image(overlay_path).convert_alpha(),
            (relative_rect[2], relative_rect[3]),
        )

        self.overlay = pygame_gui.elements.UIImage(
            relative_rect, image, manager=manager
        )

    def kill(self):
        self.status_bar.kill()
        self.overlay.kill()
        del self


class IDImageButton(UIImageButton):
    """Class to handle the "involved cats" button on the events page. It stores the IDs of the cat's involved."""

    def __init__(
            self,
            relative_rect,
            text="",
            ids=None,
            object_id=None,
            container=None,
            manager=None,
            layer_starting_height=1,
    ):

        if ids:
            self.ids = ids
        else:
            self.ids = None

        super().__init__(
            relative_rect,
            text,
            object_id=object_id,
            container=container,
            starting_height=layer_starting_height,
            manager=manager,
        )
        # This button will auto-disable if no ids are entered.
        if not self.ids:
            self.disable()


class UIDropDownContainer(UIAutoResizingContainer):

    def __init__(
            self,
            relative_rect:
            RectLike,
            container: UIContainer,
            object_id: str,
            starting_height: int,
            parent_button: UIImageButton,
            child_button_container: UIContainer,
            visible: bool,
            manager: IUIManagerInterface):
        self.parent_button = parent_button
        self.child_button_container = child_button_container

        self.is_open: bool = False
        self.selected_element = None

        super().__init__(relative_rect=relative_rect, container=container, object_id=object_id,
                         starting_height=starting_height, visible=visible, manager=manager)

    def close(self):
        """
        closes the dropdown
        """
        self.child_button_container.hide()
        self.is_open = False

    def open(self):
        """
        opens the dropdown
        """
        self.child_button_container.show()
        self.is_open = True

    def disable_child(self, button):
        """
        disables the given element and enables all other children
        """

        button.disable()
        self.selected_element = button

        for child in self.child_button_container.elements:
            child.enable()


class UICheckbox(UIImageButton):
    """
    Creates a checkbox and allows for easy check and uncheck
    """

    def __init__(
            self,
            position: tuple,
            text: str,
            container: UIContainer,
            tool_tip_text: str,
            starting_height: int,
            visible: bool,
            check: bool,
            manager,
    ):

        self.checked = False

        relative_rect = scale(pygame.Rect(position, (68, 68)))

        if check:
            object_id = "#unchecked_checkbox"
        else:
            object_id = "#checked_checkbox"

        super().__init__(relative_rect=relative_rect, text=text, container=container, tool_tip_text=tool_tip_text,
                         starting_height=starting_height, visible=visible, manager=manager, object_id=object_id)

    def check(self):
        """
        switches the checkbox into the "checked" state
        """
        self.checked = True
        self.change_object_id("#checked_checkbox")

    def uncheck(self):
        """
        switches the checkbox into the "unchecked" state
        """
        self.checked = False
        self.change_object_id("#unchecked_checkbox")


class DisplayCatList(UIAutoResizingContainer):

    def __init__(
            self,
            relative_rect: RectLike,
            container: UIContainer,
            starting_height: int,
            object_id: str,
            manager,
            cat_list: list,
            cats_displayed: int,
            px_between: int,
            columns: int,
            next_button: UIImageButton,
            prev_button: UIImageButton,
            current_page: int,
            tool_tip_name: bool
    ):
        self.cat_list = cat_list
        self.cats_displayed = cats_displayed
        self.px_between = px_between
        self.columns = columns
        self.current_page = current_page
        self.next_button = next_button
        self.prev_button = prev_button
        self.tool_tip_name = tool_tip_name

        self.cat_sprites = {}

        super().__init__(relative_rect=relative_rect, container=container, starting_height=starting_height,
                         object_id=object_id, manager=manager)

        self._display_cats()

    def update_display(self, page_number):
        """
        updates current_page and refreshes the cat display
        """

        self.current_page = page_number
        self._display_cats()

    def _display_cats(self):
        """
        creates the cat display
        """
        cat_chunks = [
            self.cat_list
            [x: x + self.cats_displayed]
            for x
            in range(0, len(self.cat_list), self.cats_displayed)
        ]

        self.current_page = max(1, min(self.current_page, len(cat_chunks)))

        self._update_arrow_buttons(cat_chunks)

        display_cats = []
        if cat_chunks:
            display_cats = cat_chunks[self.current_page - 1]

        for ele in self.elements:
            ele.kill()

        pos_x = 0
        pos_y = 0
        i = 0

        for kitty in display_cats:
            self.cat_sprites[f"sprite{i}"] = UISpriteButton(
                scale(pygame.Rect((pos_x, pos_y), (100, 100))),
                kitty.sprite,
                cat_object=kitty,
                container=self,
                object_id=f"#sprite{str(i)}",
                tool_tip_text=str(kitty.name) if self.tool_tip_name else None,
                starting_height=1
            )

            # changing position
            pos_x += self.px_between
            if pos_x >= ((self.px_between + 100) * i):
                pos_x = 0
                pos_y += self.px_between

            i += 1

    def _update_arrow_buttons(self, cat_chunks):
        """
        enables/disables appropriate arrow buttons
        """
        if len(cat_chunks) <= 1:
            self.prev_button.disable()
            self.next_button.disable()
        elif self.current_page >= len(cat_chunks):
            self.prev_button.enable()
            self.next_button.disable()
        elif self.current_page == 1 and len(cat_chunks) > 1:
            self.prev_button.disable()
            self.next_button.enable()
        else:
            self.prev_button.enable()
            self.next_button.enable()
