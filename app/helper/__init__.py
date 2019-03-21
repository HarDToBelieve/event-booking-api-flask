def allowed_image(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}


def allowed_csv(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'csv'}
