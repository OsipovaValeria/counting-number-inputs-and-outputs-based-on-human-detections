import json


# Масштабирование координат
def scale_coordinates(old_coord1, old_coord2, orig_width, orig_height, new_width, new_height):
    scaled_x = int(old_coord1 * new_width / orig_width)
    scaled_y = int(old_coord2 * new_height / orig_height)
    return scaled_x, scaled_y


def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


# Проверка на пересечение линий
def line_intersection(A, B, C, D):
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


# Проверка на пересечение "квадрата" и линии
def does_line_intersect_rectangle(line_start, line_end, rect_points):
    if line_intersection(line_start, line_end, rect_points[0], rect_points[1]):
        return True
    if line_intersection(line_start, line_end, rect_points[1], rect_points[3]):
        return True
    if line_intersection(line_start, line_end, rect_points[2], rect_points[3]):
        return True
    if line_intersection(line_start, line_end, rect_points[0], rect_points[2]):
        return True
    return False


# Вычисление средней точки
def midpoint(square):
    vertex1 = square[0]
    vertex2 = square[3]
    center_x = (vertex1[0] + vertex2[0]) / 2
    center_y = (vertex1[1] + vertex2[1]) / 2
    return center_x, center_y


# Получение координат
def get_coordinates_rectangle(data):
    return rectangle_vertices((data[0], data[1]), (data[2], data[3]))


# Координаты "квадрата"
def rectangle_vertices(top_left, bottom_right):
    x1, y1 = top_left
    x2, y2 = bottom_right

    return [(x1, y1), (x1, y2), (x2, y1), (x2, y2)]


# Получение track_id
def get_track_id(data):
    track_id = None
    for key in data[5]:
        track_id = data[5][key].get("track_id")
    return track_id


# Поиск предыдущих координат перемещения
def search_previous_move(previous_frame, current_timestamp):
    previous_data = main_path['frames'][previous_frame]['detected']['person']
    previous_timestamp = main_path['frames'][previous_frame]['timestamp']

    if current_timestamp - previous_timestamp < MAX_DIF_TIMESTAMP:

        if previous_data:

            for j in range(len(previous_data)):

                if len(previous_data[j]) > 5 and isinstance(previous_data[j][5], dict):
                    previous_track_id = get_track_id(previous_data[j])

                    if person_track_id == previous_track_id:
                        return get_coordinates_rectangle(previous_data[j])

    return


# Вычисления пересечения линии входа или выхода
def calculate_intersection_lines(current_frame, line1, line2, current_timestamp, square_coordinates, track_id,
                                 tracked_ids, count):

    if (does_line_intersect_rectangle(line1[0], line1[1], square_coordinates) and (
            midpoint(square_coordinates)[1] <= line1[1][1]) and track_id not in tracked_ids):

        for previous_frame in frames[frames.index(current_frame) - 1::-1]:

            square_previous_coordinates = search_previous_move(previous_frame, current_timestamp)

            if square_previous_coordinates:

                if (does_line_intersect_rectangle(line2[0], line2[1], square_previous_coordinates) and (
                        midpoint(square_previous_coordinates)[1] <= line2[1][1]) and track_id not in tracked_ids):
                    count = count + 1
                    tracked_ids.append(track_id)

                    break

    return count, tracked_ids


if __name__ == "__main__":

    with open('detections.json', 'r') as f:
        detections = json.load(f)

    main_path = detections['eventSpecific']['nnDetect']['10_8_3_203_rtsp_camera_3']

    int_line = []  # линия входа
    ext_line = []  # линия выхода
    box = []  # размер кадра, где были нарисованы линии
    cross_lines = main_path['cfg']['cross_lines']
    for line in cross_lines:
        ext_line.extend(line['ext_line'])
        int_line.extend(line['int_line'])
        box.extend(line['box'])

    video_frames = [main_path['cfg']['video_frames']['frame_width'], 480]

    new_ext_line = [scale_coordinates(ext_line[0], ext_line[1], box[0], box[1], video_frames[0], video_frames[1]),
                    scale_coordinates(ext_line[2], ext_line[3], box[0], box[1], video_frames[0],
                                      video_frames[1])]  # координаты линии выхода после коррекции масштаба

    new_int_line = [scale_coordinates(int_line[0], int_line[1], box[0], box[1], video_frames[0], video_frames[1]),
                    scale_coordinates(int_line[2], int_line[3], box[0], box[1], video_frames[0],
                                      video_frames[1])]  # координаты линии входа после коррекции масштаба

    MAX_DIF_TIMESTAMP = 120

    int_count, ext_count = 0, 0
    int_tracked_ids = []  # Отслеживание id входящих людей
    ext_tracked_ids = []  # Отслеживание id выходящих людей

    frames = list(main_path['frames'].keys())  # список всех кадров

    for frame in frames:

        timestamp = main_path['frames'][frame]['timestamp']
        person_data = main_path['frames'][frame]['detected']['person']

        if person_data:

            for i in range(len(person_data)):

                if len(person_data[i]) > 5 and isinstance(person_data[i][5], dict):
                    person_track_id = get_track_id(person_data[i])

                    person_square_coordinates = get_coordinates_rectangle(person_data[i])

                    # ВХОД
                    int_count, int_tracked_ids = calculate_intersection_lines(frame, new_int_line, new_ext_line,
                                                                              timestamp, person_square_coordinates,
                                                                              person_track_id, int_tracked_ids,
                                                                              int_count)

                    # ВЫХОД
                    ext_count, ext_tracked_ids = calculate_intersection_lines(frame, new_ext_line, new_int_line,
                                                                              timestamp, person_square_coordinates,
                                                                              person_track_id, ext_tracked_ids,
                                                                              ext_count)

    print('\nВход: ' + str(int_count))

    print('Выход: ' + str(ext_count))
